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
