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
