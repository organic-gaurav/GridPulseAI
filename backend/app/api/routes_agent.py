import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import agent_graph
from app.database import get_db
from app.models.db_models import AgentDecisionRecord, PolicyRecord
from app.models.schemas import AgentDecision, AnomalyItem, ConstraintPatch, PolicyRequest, ReasoningTrace
from app.services.anomaly_detector import anomaly_detector
from app.services.digital_twin import twin

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/policy", response_model=AgentDecision)
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
    res = await db.execute(select(AgentDecisionRecord).order_by(AgentDecisionRecord.created_at.desc()).limit(30))
    rows = res.scalars().all()
    items = []
    for r in rows:
        items.append(
            AgentDecision(
                id=r.id,
                created_at=r.created_at.strftime("%H:%M:%S UTC"),
                title=r.title,
                tier=r.tier,
                status=r.status,  # type: ignore
                rationale=r.rationale,
                cost_impact_usd=r.cost_impact_usd,
                carbon_impact_kg=r.carbon_impact_kg,
                comfort_impact=r.comfort_impact,
                trace=ReasoningTrace(**json.loads(r.trace_json)),
            )
        )
    return items


@router.post("/decisions/{decision_id}/approve", response_model=AgentDecision)
async def approve_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AgentDecisionRecord).where(AgentDecisionRecord.id == decision_id))
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Decision not found")
    rec.status = "approved"
    patch = ConstraintPatch(**json.loads(rec.patch_json))
    twin.apply_constraint_patch(patch)
    await db.commit()
    return AgentDecision(
        id=rec.id,
        created_at=rec.created_at.strftime("%H:%M:%S UTC"),
        title=rec.title,
        tier=rec.tier,
        status="approved",
        rationale=rec.rationale,
        cost_impact_usd=rec.cost_impact_usd,
        carbon_impact_kg=rec.carbon_impact_kg,
        comfort_impact=rec.comfort_impact,
        trace=ReasoningTrace(**json.loads(rec.trace_json)),
    )


@router.post("/decisions/{decision_id}/reject", response_model=AgentDecision)
async def reject_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AgentDecisionRecord).where(AgentDecisionRecord.id == decision_id))
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Decision not found")
    rec.status = "rejected"
    await db.commit()
    return AgentDecision(
        id=rec.id,
        created_at=rec.created_at.strftime("%H:%M:%S UTC"),
        title=rec.title,
        tier=rec.tier,
        status="rejected",
        rationale=rec.rationale,
        cost_impact_usd=rec.cost_impact_usd,
        carbon_impact_kg=rec.carbon_impact_kg,
        comfort_impact=rec.comfort_impact,
        trace=ReasoningTrace(**json.loads(rec.trace_json)),
    )


@router.get("/anomalies", response_model=List[AnomalyItem])
async def get_anomalies():
    return anomaly_detector.inspect(twin)
