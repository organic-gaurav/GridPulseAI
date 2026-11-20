from app.agent.guardrails import guardrail
from app.models.schemas import ConstraintPatch


def test_tier1_vs_tier2_guardrails():
    p1 = ConstraintPatch(battery_min_soc_pct=30.0, pareto_alpha=0.2, summary="Reserve 30%")
    tier1, _, clamped1 = guardrail.classify_and_validate(p1)
    assert tier1 == 1
    assert clamped1.battery_min_soc_pct == 30.0

    p2 = ConstraintPatch(zone_temp_overrides={"Zone A": {"t_min": 14.0, "t_max": 30.0}}, summary="Widen")
    tier2, impact2, clamped2 = guardrail.classify_and_validate(p2)
    assert tier2 == 2
    assert "Thermal" in impact2
    assert clamped2.zone_temp_overrides["Zone A"]["t_min"] == 18.0
    assert clamped2.zone_temp_overrides["Zone A"]["t_max"] == 26.5
