from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


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
    pareto_alpha: float  # 0.0 = Carbon-Zero, 1.0 = Cost-First
    active_chaos: List[str]
    feed_status: FeedStatus

    # Live Power Flows (kW)
    pv_kw: float
    grid_import_kw: float
    base_grid_import_kw: float
    battery_power_kw: float  # positive = discharging, negative = charging
    battery_soc_pct: float
    battery_capacity_kwh: float
    hvac_total_kw: float
    ev_total_kw: float
    base_load_kw: float
    deferrable_kw: float
    outdoor_temp_c: float
    carbon_intensity: float
    tariff_usd_kwh: float

    # Cumulative KPIs
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

    # Subsystems
    zones: List[ZoneState]
    ev_chargers: List[EVChargerState]
    schedule_24h: List[HourlySchedulePoint]


class ConstraintPatch(BaseModel):
    zone_temp_overrides: Optional[Dict[str, Dict[str, float]]] = None  # e.g. {"Zone A": {"t_min": 21.0, "t_max": 24.0}}
    ev_target_overrides: Optional[Dict[str, Dict[str, float]]] = None  # e.g. {"EV-1": {"departure_hour": 16, "target_kwh": 45.0}}
    battery_min_soc_pct: Optional[float] = Field(default=None, ge=15.0, le=80.0)
    pareto_alpha: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    shed_deferrable: Optional[bool] = None
    summary: str = ""


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
    tier: int  # 1 = Autonomous, 2 = HITL
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
    message: str = Field(..., min_length=2, max_length=500)


class ParetoUpdateRequest(BaseModel):
    alpha: float = Field(..., ge=0.0, le=1.0)


class ChaosRequest(BaseModel):
    event: Literal["heatwave", "cloudburst", "carbon_spike", "hvac_fault", "urgent_ev", "reset"]


class ClockControlRequest(BaseModel):
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
