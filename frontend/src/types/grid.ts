export interface ZoneState {
  zone_id: string;
  name: string;
  temp_c: number;
  t_min: number;
  t_max: number;
  occupied: boolean;
  hvac_kw: number;
  base_temp_c: number;
  base_hvac_kw: number;
}

export interface EVChargerState {
  charger_id: string;
  name: string;
  connected: boolean;
  arrival_hour: number;
  departure_hour: number;
  current_kwh: number;
  target_kwh: number;
  charge_kw: number;
  base_current_kwh: number;
  base_charge_kw: number;
}

export interface HourlySchedulePoint {
  hour: number;
  label: string;
  pv_kw: number;
  base_load_kw: number;
  hvac_kw: number;
  ev_kw: number;
  deferrable_kw: number;
  battery_charge_kw: number;
  battery_discharge_kw: number;
  battery_soc_pct: number;
  grid_import_kw: number;
  base_grid_import_kw: number;
  carbon_intensity: number;
  tariff_usd_kwh: number;
  outdoor_temp_c: number;
}

export interface FeedStatus {
  weather_source: string;
  carbon_source: string;
  ai_mode: string;
  last_updated: string;
}

export interface TwinSnapshot {
  sim_hour: number;
  is_running: boolean;
  tick_seconds: number;
  pareto_alpha: number;
  active_chaos: string[];
  feed_status: FeedStatus;
  pv_kw: number;
  grid_import_kw: number;
  base_grid_import_kw: number;
  battery_power_kw: number;
  battery_soc_pct: number;
  battery_capacity_kwh: number;
  hvac_total_kw: number;
  ev_total_kw: number;
  base_load_kw: number;
  deferrable_kw: number;
  outdoor_temp_c: number;
  carbon_intensity: number;
  tariff_usd_kwh: number;
  opt_total_cost_usd: number;
  base_total_cost_usd: number;
  cost_saved_usd: number;
  cost_saved_pct: number;
  opt_total_carbon_kg: number;
  base_total_carbon_kg: number;
  carbon_avoided_kg: number;
  carbon_avoided_pct: number;
  opt_peak_kw: number;
  base_peak_kw: number;
  peak_shaved_kw: number;
  solar_self_consumption_pct: number;
  zones: ZoneState[];
  ev_chargers: EVChargerState[];
  schedule_24h: HourlySchedulePoint[];
}

export interface ReasoningTrace {
  trigger_event: string;
  physics_check: string;
  solver_delta: string;
  guardrail_tier: string;
  rationale: string;
}

export interface AgentDecision {
  id: string;
  created_at: string;
  title: string;
  tier: number;
  status: "executed" | "pending" | "approved" | "rejected";
  rationale: string;
  cost_impact_usd: number;
  carbon_impact_kg: number;
  comfort_impact: string;
  trace: ReasoningTrace;
}

export interface AnomalyItem {
  id: string;
  detected_at: string;
  sim_hour: number;
  anomaly_type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  estimated_waste_kw: number;
  resolved: boolean;
}

export interface EsgLedgerEntry {
  hour: number;
  opt_grid_kwh: number;
  base_grid_kwh: number;
  pv_kwh: number;
  opt_cost_usd: number;
  base_cost_usd: number;
  cost_saved_usd: number;
  opt_carbon_kg: number;
  base_carbon_kg: number;
  carbon_avoided_kg: number;
}
