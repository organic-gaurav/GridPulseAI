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
