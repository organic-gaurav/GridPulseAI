import pytest
from pydantic import ValidationError

from app.agent.guardrails import guardrail
from app.models.schemas import ConstraintPatch


def test_tier1_vs_tier2_guardrails():
    tier_one = ConstraintPatch(
        battery_min_soc_pct=30.0,
        pareto_alpha=0.2,
        summary="Reserve 30%",
    )
    tier, _, validated = guardrail.classify_and_validate(tier_one)
    assert tier == 1
    assert validated.battery_min_soc_pct == 30.0

    tier_two = ConstraintPatch(
        zone_temp_overrides={
            "Zone A": {"t_min": 18.0, "t_max": 26.5}
        },
        summary="Widen occupied-zone comfort band",
    )
    tier, impact, validated = guardrail.classify_and_validate(tier_two)
    assert tier == 2
    assert "Thermal" in impact
    assert validated.zone_temp_overrides is not None
    assert validated.zone_temp_overrides["Zone A"].t_min == 18.0
    assert validated.zone_temp_overrides["Zone A"].t_max == 26.5


def test_policy_patch_rejects_out_of_bounds_and_unknown_fields():
    with pytest.raises(ValidationError):
        ConstraintPatch(
            zone_temp_overrides={
                "Zone A": {"t_min": 14.0, "t_max": 30.0}
            }
        )

    with pytest.raises(ValidationError):
        ConstraintPatch(unrecognized_control={"enabled": True})


def test_policy_patch_rejects_invalid_temperature_order():
    with pytest.raises(ValidationError):
        ConstraintPatch(
            zone_temp_overrides={
                "Zone A": {"t_min": 24.0, "t_max": 22.0}
            }
        )
