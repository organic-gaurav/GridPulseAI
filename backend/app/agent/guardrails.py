from typing import Tuple
from app.models.schemas import ConstraintPatch


class SafetyGuardrail:
    """Deterministic Tier-1 (Autonomous) vs Tier-2 (HITL Approval Required) safety validator."""

    def classify_and_validate(self, patch: ConstraintPatch) -> Tuple[int, str, ConstraintPatch]:
        """
        Returns (tier, comfort_impact, clamped_patch).
        Tier 1 (Autonomous): Battery reserve, Pareto alpha, EV deadline within bounds.
        Tier 2 (HITL): Widening/altering occupied zone temp bands or shedding loads.
        """
        tier = 1
        comfort_impact = "None (Autonomous)"

        if patch.zone_temp_overrides:
            tier = 2
            comfort_impact = "Occupied Zone Thermal Band Change"
            for zid, bounds in patch.zone_temp_overrides.items():
                if "t_min" in bounds:
                    bounds["t_min"] = max(18.0, min(24.0, float(bounds["t_min"])))
                if "t_max" in bounds:
                    bounds["t_max"] = max(20.0, min(26.5, float(bounds["t_max"])))

        if patch.shed_deferrable:
            tier = 2
            comfort_impact = "Shedding Non-Critical Deferrable Load"

        if patch.battery_min_soc_pct is not None:
            patch.battery_min_soc_pct = max(15.0, min(80.0, float(patch.battery_min_soc_pct)))

        return tier, comfort_impact, patch


guardrail = SafetyGuardrail()
