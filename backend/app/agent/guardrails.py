from typing import Tuple

from app.models.schemas import ConstraintPatch


class SafetyGuardrail:
    """Deterministic Tier-1 vs. Tier-2 policy validator."""

    def classify_and_validate(self, patch: ConstraintPatch) -> Tuple[int, str, ConstraintPatch]:
        """
        Returns (tier, comfort_impact, validated_patch).

        Thermal-band changes and load shedding require human approval.
        Bounded battery and Pareto changes may be applied autonomously.
        """
        tier = 1
        comfort_impact = "None (Autonomous)"

        if patch.zone_temp_overrides:
            tier = 2
            comfort_impact = "Occupied Zone Thermal Band Change"
            for bounds in patch.zone_temp_overrides.values():
                if bounds.t_min is not None:
                    bounds.t_min = max(18.0, min(24.0, float(bounds.t_min)))
                if bounds.t_max is not None:
                    bounds.t_max = max(20.0, min(26.5, float(bounds.t_max)))

        if patch.shed_deferrable:
            tier = 2
            comfort_impact = "Shedding Non-Critical Deferrable Load"

        if patch.battery_min_soc_pct is not None:
            patch.battery_min_soc_pct = max(15.0, min(80.0, float(patch.battery_min_soc_pct)))

        return tier, comfort_impact, patch


guardrail = SafetyGuardrail()
