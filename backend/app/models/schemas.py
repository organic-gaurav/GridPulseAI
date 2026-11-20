from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ZoneState(BaseModel):
    zone_id: str
    name: str
    temp_c: float
    t_min: float
    t_max: float
    occupied: bool
    hvac_kw: float
    base_temp_c: float
    base_hvac_kw: float


class EVChargerState(BaseModel):
    charger_id: str
    name: str
    connected: bool
    arrival_hour: int
    departure_hour: int
    current_kwh: float
    target_kwh: float
    charge_kw: float
    base_current_kwh: float
    base_charge_kw: float


class HourlySchedulePoint(BaseModel):
    hour: int
    label: str
    pv_kw: float
    base_load_kw: float
    hvac_kw: float
    ev_kw: float
    deferrable_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    battery_soc_pct: float
    grid_import_kw: float
    base_grid_import_kw: float
    carbon_intensity: float
    tariff_usd_kwh: float
    outdoor_temp_c: float


class FeedStatus(BaseModel):
    weather_source: str
    carbon_source: str
    ai_mode: str
    last_updated: str


class TwinSnapshot(BaseModel):
    sim_hour: int
    is_running: bool
    tick_seconds: float
    pareto_alpha: float
    active_chaos: List[str]
    feed_status: FeedStatus

    pv_kw: float
    grid_import_kw: float
    base_grid_import_kw: float
    battery_power_kw: float
    battery_soc_pct: float
    battery_capacity_kwh: float
    hvac_total_kw: float
    ev_total_kw: float
    base_load_kw: float
    deferrable_kw: float
    outdoor_temp_c: float
    carbon_intensity: float
    tariff_usd_kwh: float

    opt_total_cost_usd: float
    base_total_cost_usd: float
    cost_saved_usd: float
    cost_saved_pct: float

    opt_total_carbon_kg: float
    base_total_carbon_kg: float
    carbon_avoided_kg: float
    carbon_avoided_pct: float

    opt_peak_kw: float
    base_peak_kw: float
    peak_shaved_kw: float
    solar_self_consumption_pct: float

    zones: List[ZoneState]
    ev_chargers: List[EVChargerState]
    schedule_24h: List[HourlySchedulePoint]


class ZoneTempOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    t_min: Optional[float] = Field(default=None, ge=18.0, le=24.0)
    t_max: Optional[float] = Field(default=None, ge=20.0, le=26.5)

    @model_validator(mode="after")
    def validate_temperature_band(self):
        if self.t_min is not None and self.t_max is not None and self.t_min >= self.t_max:
            raise ValueError("t_min must be lower than t_max")
        return self


class EVTargetOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    departure_hour: Optional[int] = Field(default=None, ge=1, le=23)
    target_kwh: Optional[float] = Field(default=None, ge=10.0, le=80.0)


class ConstraintPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    zone_temp_overrides: Optional[
        Dict[Literal["Zone A", "Zone B", "Zone C"], ZoneTempOverride]
    ] = None
    ev_target_overrides: Optional[
        Dict[Literal["EV-1", "EV-2", "EV-3"], EVTargetOverride]
    ] = None
    battery_min_soc_pct: Optional[float] = Field(default=None, ge=15.0, le=80.0)
    pareto_alpha: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    shed_deferrable: Optional[bool] = None
    summary: str = Field(default="", max_length=500)


class ReasoningTrace(BaseModel):
    trigger_event: str
    physics_check: str
    solver_delta: str
    guardrail_tier: str
    rationale: str


class AgentDecision(BaseModel):
    id: str
    created_at: str
    title: str
    tier: int
    status: Literal["executed", "pending", "approved", "rejected"]
    rationale: str
    cost_impact_usd: float
    carbon_impact_kg: float
    comfort_impact: str
    trace: ReasoningTrace


class AnomalyItem(BaseModel):
    id: str
    detected_at: str
    sim_hour: int
    anomaly_type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    estimated_waste_kw: float
    resolved: bool


class PolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(..., min_length=2, max_length=500)


class ParetoUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    alpha: float = Field(..., ge=0.0, le=1.0)


class ChaosRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: Literal["heatwave", "cloudburst", "carbon_spike", "hvac_fault", "urgent_ev", "reset"]


class ClockControlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    action: Literal["play", "pause", "step", "reset"]
    tick_seconds: Optional[float] = Field(default=None, ge=0.5, le=10.0)


class EsgLedgerEntry(BaseModel):
    hour: int
    opt_grid_kwh: float
    base_grid_kwh: float
    pv_kwh: float
    opt_cost_usd: float
    base_cost_usd: float
    cost_saved_usd: float
    opt_carbon_kg: float
    base_carbon_kg: float
    carbon_avoided_kg: float
