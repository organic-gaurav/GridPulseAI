import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import agent_graph
from app.database import get_db
from app.models.db_models import AgentDecisionRecord, PolicyRecord
from app.models.schemas import (
    AgentDecision,
    AnomalyItem,
    ConstraintPatch,
    PolicyRequest,
    ReasoningTrace,
)
from app.security import require_operator
from app.services.anomaly_detector import anomaly_detector
from app.services.digital_twin import twin

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/policy", response_model=AgentDecision, dependencies=[Depends(require_operator)])
async def submit_policy(req: PolicyRequest, db: AsyncSession = Depends(get_db)):
    result = await agent_graph.ainvoke(
        {
            "message": req.message,
            "patch": None,
            "tier": 1,
            "comfort_impact": "None",
            "cost_impact_usd": 0.0,
            "carbon_impact_kg": 0.0,
            "decision": None,
        }
    )
    decision: AgentDecision = result["decision"]
    patch: ConstraintPatch = result["patch"]

    db.add(
        AgentDecisionRecord(
            id=decision.id,
            title=decision.title,
            tier=decision.tier,
            status=decision.status,
            rationale=decision.rationale,
            cost_impact_usd=decision.cost_impact_usd,
            carbon_impact_kg=decision.carbon_impact_kg,
            comfort_impact=decision.comfort_impact,
            trace_json=decision.trace.model_dump_json(),
            patch_json=patch.model_dump_json(),
        )
    )
    db.add(PolicyRecord(raw_text=req.message, parsed_json=patch.model_dump_json(), active=True))
    await db.commit()
    return decision


@router.get("/decisions", response_model=List[AgentDecision])
async def list_decisions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentDecisionRecord)
        .order_by(AgentDecisionRecord.created_at.desc())
        .limit(30)
    )
    rows = result.scalars().all()
    return [
        AgentDecision(
            id=row.id,
            created_at=row.created_at.strftime("%H:%M:%S UTC"),
            title=row.title,
            tier=row.tier,
            status=row.status,  # type: ignore[arg-type]
            rationale=row.rationale,
            cost_impact_usd=row.cost_impact_usd,
            carbon_impact_kg=row.carbon_impact_kg,
            comfort_impact=row.comfort_impact,
            trace=ReasoningTrace(**json.loads(row.trace_json)),
        )
        for row in rows
    ]


def _decision_response(record: AgentDecisionRecord, status: str) -> AgentDecision:
    return AgentDecision(
        id=record.id,
        created_at=record.created_at.strftime("%H:%M:%S UTC"),
        title=record.title,
        tier=record.tier,
        status=status,  # type: ignore[arg-type]
        rationale=record.rationale,
        cost_impact_usd=record.cost_impact_usd,
        carbon_impact_kg=record.carbon_impact_kg,
        comfort_impact=record.comfort_impact,
        trace=ReasoningTrace(**json.loads(record.trace_json)),
    )


async def _get_pending_human_decision(
    decision_id: str,
    db: AsyncSession,
) -> AgentDecisionRecord:
    result = await db.execute(
        select(AgentDecisionRecord).where(AgentDecisionRecord.id == decision_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    if record.tier != 2 or record.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending Tier-2 decisions can be approved or rejected",
        )
    return record


@router.post(
    "/decisions/{decision_id}/approve",
    response_model=AgentDecision,
    dependencies=[Depends(require_operator)],
)
async def approve_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    record = await _get_pending_human_decision(decision_id, db)
    patch = ConstraintPatch.model_validate_json(record.patch_json)
    twin.apply_constraint_patch(patch)
    record.status = "approved"
    await db.commit()
    return _decision_response(record, "approved")


@router.post(
    "/decisions/{decision_id}/reject",
    response_model=AgentDecision,
    dependencies=[Depends(require_operator)],
)
async def reject_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    record = await _get_pending_human_decision(decision_id, db)
    record.status = "rejected"
    await db.commit()
    return _decision_response(record, "rejected")


@router.get("/anomalies", response_model=List[AnomalyItem])
async def get_anomalies():
    return anomaly_detector.inspect(twin)
