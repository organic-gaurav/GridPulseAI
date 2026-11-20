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
