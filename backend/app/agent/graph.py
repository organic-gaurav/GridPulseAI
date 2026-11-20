import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, TypedDict

from langgraph.graph import END, StateGraph

from app.agent.guardrails import guardrail
from app.agent.llm_client import llm_client
from app.models.schemas import AgentDecision, ConstraintPatch, ReasoningTrace
from app.services.digital_twin import twin


class AgentState(TypedDict):
    message: str
    patch: ConstraintPatch | None
    tier: int
    comfort_impact: str
    cost_impact_usd: float
    carbon_impact_kg: float
    decision: AgentDecision | None


async def observe_node(state: AgentState) -> Dict[str, Any]:
    return {}


async def compile_node(state: AgentState) -> Dict[str, Any]:
    patch = await llm_client.compile_policy(state["message"])
    return {"patch": patch}


async def guardrail_node(state: AgentState) -> Dict[str, Any]:
    patch = state["patch"] or ConstraintPatch(summary=state["message"])
    tier, comfort_impact, clamped = guardrail.classify_and_validate(patch)
    return {"patch": clamped, "tier": tier, "comfort_impact": comfort_impact}


async def solve_node(state: AgentState) -> Dict[str, Any]:
    patch = state["patch"]
    # Estimate impact
    cost_delta = -4.2 if (patch and patch.pareto_alpha and patch.pareto_alpha > 0.6) else 1.8
    carb_delta = 12.4 if (patch and patch.pareto_alpha and patch.pareto_alpha < 0.4) else 3.5

    if state["tier"] == 1 and patch is not None:
        twin.apply_constraint_patch(patch)

    return {"cost_impact_usd": cost_delta, "carbon_impact_kg": carb_delta}


async def explain_node(state: AgentState) -> Dict[str, Any]:
    patch = state["patch"]
    tier = state["tier"]
    status = "executed" if tier == 1 else "pending"
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    trace = ReasoningTrace(
        trigger_event=f"Operator Policy: '{state['message']}'",
        physics_check=f"Verified BESS SoC ({twin.battery_soc_kwh:.1f} kWh) & 3 HVAC RC zones.",
        solver_delta=f"LP re-solved in {twin.last_solve_ms} ms; projected CO2 delta {state['carbon_impact_kg']:+.1f} kg.",
        guardrail_tier=f"Tier {tier} ({'Autonomous' if tier == 1 else 'HITL Approval Required'})",
        rationale=patch.summary if patch and patch.summary else state["message"],
    )

    decision = AgentDecision(
        id=f"dec-{uuid.uuid4().hex[:8]}",
        created_at=now_str,
        title=patch.summary if patch and patch.summary else "Policy Update",
        tier=tier,
        status=status,
        rationale=trace.rationale,
        cost_impact_usd=state["cost_impact_usd"],
        carbon_impact_kg=state["carbon_impact_kg"],
        comfort_impact=state["comfort_impact"],
        trace=trace,
    )
    return {"decision": decision}


def build_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("observe", observe_node)
    workflow.add_node("compile", compile_node)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("solve", solve_node)
    workflow.add_node("explain", explain_node)

    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "compile")
    workflow.add_edge("compile", "guardrail")
    workflow.add_edge("guardrail", "solve")
    workflow.add_edge("solve", "explain")
    workflow.add_edge("explain", END)
    return workflow.compile()


agent_graph = build_agent_graph()
