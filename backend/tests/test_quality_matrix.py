"""Focused regression tests for GridPulse AI's safety and data contracts."""

import csv
import io
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.agent.guardrails import SafetyGuardrail
from app.agent.llm_client import LLMClient
from app.config import Settings, settings
from app.security import require_operator
from app.models.schemas import (
    ChaosRequest,
    ClockControlRequest,
    ConstraintPatch,
    EVTargetOverride,
    EsgLedgerEntry,
    ParetoUpdateRequest,
    PolicyRequest,
    ZoneTempOverride,
)
from app.services.anomaly_detector import AnomalyDetector
from app.services.digital_twin import DualDigitalTwin
from app.services.esg_ledger import ledger_to_csv


def test_default_settings_use_valid_demo_coordinates():
    settings = Settings(_env_file=None)
    assert -90 <= settings.latitude <= 90
    assert -180 <= settings.longitude <= 180
    assert settings.environment == "development"


def test_default_frontend_origin_is_localhost():
    assert Settings(_env_file=None).frontend_origin == "http://localhost:5173"


def test_default_carbon_provider_is_uk():
    assert Settings(_env_file=None).carbon_provider == "uk_carbon"


def test_operator_token_alias_maps_to_gridpulse_api_token():
    configured = Settings(GRIDPULSE_API_TOKEN="test-secret", _env_file=None)
    assert configured.api_access_token == "test-secret"


def test_ai_mode_uses_deterministic_fallback_without_provider_key():
    configured = Settings(openai_api_key="", groq_api_key="", gemini_api_key="", _env_file=None)
    assert configured.ai_mode == "Deterministic Fallback"


def test_ai_mode_reports_live_llm_when_provider_key_exists():
    configured = Settings(openai_api_key="openai-test", _env_file=None)
    assert configured.ai_mode == "Live LLM"


def test_openai_key_has_priority_over_other_provider_keys():
    configured = Settings(openai_api_key="openai", groq_api_key="groq", gemini_api_key="gemini", _env_file=None)
    assert configured.active_llm_key == "openai"


def test_groq_key_is_selected_when_openai_key_is_missing():
    configured = Settings(groq_api_key="groq", gemini_api_key="gemini", _env_file=None)
    assert configured.active_llm_key == "groq"


def test_gemini_key_is_selected_when_other_provider_keys_are_missing():
    configured = Settings(gemini_api_key="gemini", _env_file=None)
    assert configured.active_llm_key == "gemini"


def test_zone_temperature_schema_accepts_documented_limits():
    zone = ZoneTempOverride(t_min=18.0, t_max=26.5)
    assert (zone.t_min, zone.t_max) == (18.0, 26.5)


def test_zone_temperature_schema_rejects_too_low_minimum():
    with pytest.raises(ValidationError):
        ZoneTempOverride(t_min=17.99)


def test_zone_temperature_schema_rejects_too_high_maximum():
    with pytest.raises(ValidationError):
        ZoneTempOverride(t_max=26.51)


def test_zone_temperature_schema_rejects_reversed_band():
    with pytest.raises(ValidationError):
        ZoneTempOverride(t_min=24.0, t_max=22.0)


def test_zone_temperature_schema_rejects_infinite_temperature():
    with pytest.raises(ValidationError):
        ZoneTempOverride(t_min=float("inf"))


def test_zone_temperature_schema_allows_minimum_only_patch():
    assert ZoneTempOverride(t_min=19.0).t_min == 19.0


def test_zone_temperature_schema_allows_maximum_only_patch():
    assert ZoneTempOverride(t_max=25.0).t_max == 25.0


def test_ev_target_schema_accepts_departure_hour_boundaries():
    assert EVTargetOverride(departure_hour=1, target_kwh=10).departure_hour == 1
    assert EVTargetOverride(departure_hour=23, target_kwh=80).target_kwh == 80


def test_ev_target_schema_rejects_departure_before_one():
    with pytest.raises(ValidationError):
        EVTargetOverride(departure_hour=0)


def test_ev_target_schema_rejects_departure_after_twenty_three():
    with pytest.raises(ValidationError):
        EVTargetOverride(departure_hour=24)


def test_ev_target_schema_rejects_target_below_ten_kwh():
    with pytest.raises(ValidationError):
        EVTargetOverride(target_kwh=9.9)


def test_ev_target_schema_rejects_target_above_eighty_kwh():
    with pytest.raises(ValidationError):
        EVTargetOverride(target_kwh=80.1)


def test_constraint_patch_accepts_known_zone_identifier():
    patch = ConstraintPatch(zone_temp_overrides={"Zone A": {"t_min": 20.0}})
    assert patch.zone_temp_overrides["Zone A"].t_min == 20.0


def test_constraint_patch_rejects_unknown_zone_identifier():
    with pytest.raises(ValidationError):
        ConstraintPatch(zone_temp_overrides={"Zone D": {"t_min": 20.0}})


def test_constraint_patch_accepts_known_ev_identifier():
    patch = ConstraintPatch(ev_target_overrides={"EV-2": {"departure_hour": 18}})
    assert patch.ev_target_overrides["EV-2"].departure_hour == 18


def test_constraint_patch_rejects_unknown_ev_identifier():
    with pytest.raises(ValidationError):
        ConstraintPatch(ev_target_overrides={"EV-9": {"departure_hour": 18}})


def test_constraint_patch_rejects_battery_reserve_below_safety_floor():
    with pytest.raises(ValidationError):
        ConstraintPatch(battery_min_soc_pct=14.9)


def test_constraint_patch_rejects_battery_reserve_above_policy_limit():
    with pytest.raises(ValidationError):
        ConstraintPatch(battery_min_soc_pct=80.1)


def test_constraint_patch_accepts_battery_reserve_boundaries():
    assert ConstraintPatch(battery_min_soc_pct=15).battery_min_soc_pct == 15
    assert ConstraintPatch(battery_min_soc_pct=80).battery_min_soc_pct == 80


def test_constraint_patch_accepts_pareto_alpha_endpoints():
    assert ConstraintPatch(pareto_alpha=0).pareto_alpha == 0
    assert ConstraintPatch(pareto_alpha=1).pareto_alpha == 1


def test_constraint_patch_rejects_pareto_alpha_below_zero():
    with pytest.raises(ValidationError):
        ConstraintPatch(pareto_alpha=-0.01)


def test_constraint_patch_rejects_pareto_alpha_above_one():
    with pytest.raises(ValidationError):
        ConstraintPatch(pareto_alpha=1.01)


def test_constraint_patch_rejects_unknown_control_fields():
    with pytest.raises(ValidationError):
        ConstraintPatch(unapproved_switch=True)


def test_constraint_patch_rejects_summary_longer_than_five_hundred_chars():
    with pytest.raises(ValidationError):
        ConstraintPatch(summary="x" * 501)


def test_policy_request_strips_surrounding_whitespace():
    request = PolicyRequest(message="  prioritize solar  ")
    assert request.message == "prioritize solar"


def test_policy_request_rejects_one_character_message():
    with pytest.raises(ValidationError):
        PolicyRequest(message="x")


def test_policy_request_rejects_message_over_five_hundred_chars():
    with pytest.raises(ValidationError):
        PolicyRequest(message="x" * 501)


def test_policy_request_rejects_unrecognized_fields():
    with pytest.raises(ValidationError):
        PolicyRequest(message="prioritize solar", admin=True)


def test_pareto_request_accepts_zero_and_one():
    assert ParetoUpdateRequest(alpha=0).alpha == 0
    assert ParetoUpdateRequest(alpha=1).alpha == 1


def test_pareto_request_rejects_alpha_outside_unit_interval():
    with pytest.raises(ValidationError):
        ParetoUpdateRequest(alpha=1.001)


def test_pareto_request_rejects_non_finite_alpha():
    with pytest.raises(ValidationError):
        ParetoUpdateRequest(alpha=float("nan"))


def test_chaos_request_accepts_reset_event():
    assert ChaosRequest(event="reset").event == "reset"


def test_chaos_request_rejects_unknown_event():
    with pytest.raises(ValidationError):
        ChaosRequest(event="power_cut")


def test_clock_request_accepts_each_documented_action():
    for action in ("play", "pause", "step", "reset"):
        assert ClockControlRequest(action=action).action == action


def test_clock_request_rejects_unknown_action():
    with pytest.raises(ValidationError):
        ClockControlRequest(action="fast_forward")


def test_clock_request_accepts_tick_interval_endpoints():
    assert ClockControlRequest(action="play", tick_seconds=0.5).tick_seconds == 0.5
    assert ClockControlRequest(action="play", tick_seconds=10).tick_seconds == 10


def test_clock_request_rejects_tick_interval_below_minimum():
    with pytest.raises(ValidationError):
        ClockControlRequest(action="play", tick_seconds=0.49)


def test_clock_request_rejects_tick_interval_above_maximum():
    with pytest.raises(ValidationError):
        ClockControlRequest(action="play", tick_seconds=10.01)


def test_empty_policy_patch_is_classified_as_autonomous():
    tier, impact, _ = SafetyGuardrail().classify_and_validate(ConstraintPatch())
    assert tier == 1
    assert impact == "None (Autonomous)"


def test_temperature_override_requires_human_approval():
    patch = ConstraintPatch(zone_temp_overrides={"Zone A": {"t_min": 20.0}})
    tier, impact, _ = SafetyGuardrail().classify_and_validate(patch)
    assert tier == 2
    assert "Thermal" in impact


def test_deferrable_load_shedding_requires_human_approval():
    tier, impact, _ = SafetyGuardrail().classify_and_validate(ConstraintPatch(shed_deferrable=True))
    assert tier == 2
    assert "Shedding" in impact


def test_battery_reserve_only_patch_remains_tier_one():
    tier, _, patch = SafetyGuardrail().classify_and_validate(ConstraintPatch(battery_min_soc_pct=35))
    assert tier == 1
    assert patch.battery_min_soc_pct == 35


def test_pareto_weight_only_patch_remains_tier_one():
    tier, _, patch = SafetyGuardrail().classify_and_validate(ConstraintPatch(pareto_alpha=0.25))
    assert tier == 1
    assert patch.pareto_alpha == 0.25


def test_zone_override_with_only_maximum_is_tier_two():
    patch = ConstraintPatch(zone_temp_overrides={"Zone B": {"t_max": 25.0}})
    tier, _, _ = SafetyGuardrail().classify_and_validate(patch)
    assert tier == 2


def test_load_shedding_reason_is_specific_when_combined_with_zone_change():
    patch = ConstraintPatch(zone_temp_overrides={"Zone A": {"t_min": 20.0}}, shed_deferrable=True)
    _, impact, _ = SafetyGuardrail().classify_and_validate(patch)
    assert impact == "Shedding Non-Critical Deferrable Load"


def test_deterministic_parser_prioritizes_carbon():
    patch = LLMClient()._deterministic_parse("prioritize carbon reduction")
    assert patch.pareto_alpha == 0.1


def test_deterministic_parser_maps_cost_priority_to_high_alpha():
    patch = LLMClient()._deterministic_parse("reduce the electricity bill and save money")
    assert patch.pareto_alpha == 0.9


def test_deterministic_parser_extracts_battery_reserve_percentage():
    patch = LLMClient()._deterministic_parse("set battery reserve to 30%")
    assert patch.battery_min_soc_pct == 30.0


def test_deterministic_parser_clamps_low_battery_reserve_to_safety_floor():
    patch = LLMClient()._deterministic_parse("set battery reserve to 10%")
    assert patch.battery_min_soc_pct == 15.0


def test_deterministic_parser_clamps_high_battery_reserve_to_policy_ceiling():
    patch = LLMClient()._deterministic_parse("set battery reserve to 90%")
    assert patch.battery_min_soc_pct == 80.0


def test_deterministic_parser_builds_precooling_temperature_band():
    patch = LLMClient()._deterministic_parse("pre-cool Zone A before the afternoon")
    assert patch.zone_temp_overrides["Zone A"].t_min == 19.5
    assert patch.zone_temp_overrides["Zone A"].t_max == 23.0


def test_deterministic_parser_builds_wider_comfort_band():
    patch = LLMClient()._deterministic_parse("widen Zone A comfort band")
    assert patch.zone_temp_overrides["Zone A"].t_max == 26.0


def test_deterministic_parser_marks_noncritical_load_shedding():
    patch = LLMClient()._deterministic_parse("shed noncritical batch loads")
    assert patch.shed_deferrable is True


def test_deterministic_parser_uses_default_office_temperature_band():
    patch = LLMClient()._deterministic_parse("set the office temperature")
    assert patch.zone_temp_overrides["Zone A"].t_min == 21.0
    assert patch.zone_temp_overrides["Zone A"].t_max == 23.5


def test_deterministic_parser_converts_evening_ev_departure_to_twenty_four_hour_time():
    patch = LLMClient()._deterministic_parse("fleet van departure by 6pm")
    assert patch.ev_target_overrides["EV-1"].departure_hour == 18


def test_deterministic_parser_sets_ev_target_for_fleet_request():
    patch = LLMClient()._deterministic_parse("fleet van departure by 6pm")
    assert patch.ev_target_overrides["EV-1"].target_kwh == 55.0


def test_deterministic_parser_keeps_unrecognized_request_as_summary():
    patch = LLMClient()._deterministic_parse("keep the current lighting schedule")
    assert patch.summary.startswith("Parsed policy:")


@pytest.mark.asyncio
async def test_policy_compiler_uses_local_parser_when_no_llm_client_is_configured():
    client = LLMClient()
    client.client = None
    patch = await client.compile_policy("prioritize carbon")
    assert patch.pareto_alpha == 0.1


def test_digital_twin_starts_at_eight_simulation_hours():
    assert DualDigitalTwin().sim_hour == 8


def test_digital_twin_starts_paused():
    assert DualDigitalTwin().is_running is False


def test_digital_twin_initializes_twenty_four_hour_forecast_profiles():
    twin = DualDigitalTwin()
    assert len(twin.outdoor_temp_c) == len(twin.irradiance_wm2) == len(twin.carbon_intensity) == 24


def test_digital_twin_initializes_three_thermal_zones():
    assert len(DualDigitalTwin().zones) == 3


def test_digital_twin_initializes_three_ev_chargers():
    assert len(DualDigitalTwin().ev_chargers) == 3


def test_photovoltaic_profile_is_zero_without_irradiance():
    twin = DualDigitalTwin()
    twin.irradiance_wm2 = [0.0] * 24
    assert twin.compute_pv_profile() == [0.0] * 24


def test_photovoltaic_profile_reaches_rated_peak_at_reference_conditions():
    twin = DualDigitalTwin()
    twin.outdoor_temp_c = [25.0] * 24
    twin.irradiance_wm2 = [1000.0] * 24
    assert twin.compute_pv_profile() == [60.0] * 24


def test_photovoltaic_profile_applies_hot_weather_derating_floor():
    twin = DualDigitalTwin()
    twin.outdoor_temp_c = [100.0] * 24
    twin.irradiance_wm2 = [1000.0] * 24
    assert twin.compute_pv_profile()[12] == 45.0


def test_photovoltaic_profile_clamps_negative_irradiance_to_zero():
    twin = DualDigitalTwin()
    twin.irradiance_wm2 = [-100.0] * 24
    assert twin.compute_pv_profile() == [0.0] * 24


def test_digital_twin_reset_restores_default_control_parameters():
    twin = DualDigitalTwin()
    twin.pareto_alpha = 0.9
    twin.shed_deferrable = True
    twin.reset()
    assert twin.pareto_alpha == 0.5
    assert twin.shed_deferrable is False


def test_heatwave_fault_increases_forecast_temperature_by_seven_degrees(monkeypatch):
    twin = DualDigitalTwin()
    monkeypatch.setattr(twin, "reoptimize", lambda: None)
    before = list(twin.outdoor_temp_c)
    twin.inject_chaos("heatwave")
    assert twin.outdoor_temp_c == [value + 7.0 for value in before]


def test_cloudburst_fault_reduces_solar_irradiance(monkeypatch):
    twin = DualDigitalTwin()
    monkeypatch.setattr(twin, "reoptimize", lambda: None)
    before = list(twin.irradiance_wm2)
    twin.inject_chaos("cloudburst")
    assert twin.irradiance_wm2 == [round(value * 0.35, 1) for value in before]


def test_carbon_spike_fault_adds_two_hundred_fifty_grams(monkeypatch):
    twin = DualDigitalTwin()
    monkeypatch.setattr(twin, "reoptimize", lambda: None)
    before = list(twin.carbon_intensity)
    twin.inject_chaos("carbon_spike")
    assert twin.carbon_intensity == [round(value + 250.0, 1) for value in before]


def test_urgent_ev_fault_moves_ev_one_departure_four_hours_ahead(monkeypatch):
    twin = DualDigitalTwin()
    monkeypatch.setattr(twin, "reoptimize", lambda: None)
    twin.inject_chaos("urgent_ev")
    assert twin.ev_chargers[0]["departure_hour"] == twin.sim_hour + 4


def test_reset_fault_clears_active_chaos(monkeypatch):
    twin = DualDigitalTwin()
    monkeypatch.setattr(twin, "reoptimize", lambda: None)
    twin.active_chaos = ["heatwave", "cloudburst"]
    twin.inject_chaos("reset")
    assert twin.active_chaos == []


def test_baseline_hour_returns_grid_hvac_and_ev_metrics():
    twin = DualDigitalTwin()
    result = twin.compute_baseline_hour(0, 0.0)
    assert set(result) == {"grid_import_kw", "hvac_kw", "ev_kw"}
    assert result["grid_import_kw"] >= 0


def test_anomaly_detector_returns_no_alerts_for_normal_state():
    state = SimpleNamespace(active_chaos=[], sim_hour=8, schedule_24h=[], PV_PEAK_KW=60.0)
    assert AnomalyDetector().inspect(state) == []


def test_anomaly_detector_marks_hvac_fault_as_critical():
    state = SimpleNamespace(active_chaos=["hvac_fault"], sim_hour=8, schedule_24h=[], PV_PEAK_KW=60.0)
    alerts = AnomalyDetector().inspect(state)
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"


def test_anomaly_detector_marks_cloudburst_as_high_severity():
    state = SimpleNamespace(active_chaos=["cloudburst"], sim_hour=8, schedule_24h=[], PV_PEAK_KW=60.0)
    alerts = AnomalyDetector().inspect(state)
    assert alerts[0].severity == "high"
    assert alerts[0].estimated_waste_kw > 0


def test_anomaly_detector_does_not_flag_grid_import_at_exact_threshold():
    schedule = [SimpleNamespace(grid_import_kw=55.0) for _ in range(9)]
    state = SimpleNamespace(active_chaos=[], sim_hour=8, schedule_24h=schedule, PV_PEAK_KW=60.0)
    assert AnomalyDetector().inspect(state) == []


def test_anomaly_detector_flags_grid_import_above_threshold():
    schedule = [SimpleNamespace(grid_import_kw=56.0) for _ in range(9)]
    state = SimpleNamespace(active_chaos=[], sim_hour=8, schedule_24h=schedule, PV_PEAK_KW=60.0)
    alerts = AnomalyDetector().inspect(state)
    assert len(alerts) == 1
    assert alerts[0].severity == "medium"


def test_anomaly_detector_combines_independent_fault_alerts():
    schedule = [SimpleNamespace(grid_import_kw=56.0) for _ in range(9)]
    state = SimpleNamespace(active_chaos=["hvac_fault", "cloudburst"], sim_hour=8, schedule_24h=schedule, PV_PEAK_KW=60.0)
    assert len(AnomalyDetector().inspect(state)) == 3


def test_esg_csv_export_includes_expected_column_headers():
    entry = EsgLedgerEntry(hour=1, opt_grid_kwh=1, base_grid_kwh=2, pv_kwh=3, opt_cost_usd=4, base_cost_usd=5, cost_saved_usd=1, opt_carbon_kg=6, base_carbon_kg=7, carbon_avoided_kg=1)
    rows = list(csv.reader(io.StringIO(ledger_to_csv([entry]))))
    assert rows[0][0] == "Hour"
    assert rows[0][-1] == "Carbon Avoided (kg CO2eq)"


def test_esg_csv_export_serializes_one_ledger_record():
    entry = EsgLedgerEntry(hour=3, opt_grid_kwh=10, base_grid_kwh=12, pv_kwh=4, opt_cost_usd=2, base_cost_usd=3, cost_saved_usd=1, opt_carbon_kg=5, base_carbon_kg=7, carbon_avoided_kg=2)
    rows = list(csv.reader(io.StringIO(ledger_to_csv([entry]))))
    assert len(rows) == 2
    assert rows[1][0] == "3"


def test_esg_csv_export_preserves_decimal_precision():
    entry = EsgLedgerEntry(hour=4, opt_grid_kwh=12.75, base_grid_kwh=13.25, pv_kwh=5.5, opt_cost_usd=1.25, base_cost_usd=1.75, cost_saved_usd=0.5, opt_carbon_kg=2.25, base_carbon_kg=3.75, carbon_avoided_kg=1.5)
    rows = list(csv.reader(io.StringIO(ledger_to_csv([entry]))))
    assert rows[1][1:4] == ["12.75", "13.25", "5.5"]


@pytest.mark.asyncio
async def test_operator_access_allows_local_development_without_token(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "api_access_token", "")
    await require_operator(None)


@pytest.mark.asyncio
async def test_operator_access_fails_closed_in_production_without_token(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "")
    with pytest.raises(HTTPException) as error:
        await require_operator(None)
    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_operator_access_rejects_missing_credentials_in_production(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "configured-secret")
    with pytest.raises(HTTPException) as error:
        await require_operator(None)
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_operator_access_rejects_incorrect_token(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "configured-secret")
    with pytest.raises(HTTPException) as error:
        await require_operator(SimpleNamespace(credentials="wrong-secret"))
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_operator_access_accepts_exact_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "configured-secret")
    await require_operator(SimpleNamespace(credentials="configured-secret"))


@pytest.mark.asyncio
async def test_operator_access_does_not_trim_or_normalize_supplied_token(monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "configured-secret")
    with pytest.raises(HTTPException):
        await require_operator(SimpleNamespace(credentials=" configured-secret "))
