import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_api_endpoints():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        state_response = client.get("/api/twin/state")
        assert state_response.status_code == 200
        data = state_response.json()
        assert "schedule_24h" in data
        assert len(data["schedule_24h"]) == 24

        pareto_response = client.post("/api/optimizer/pareto", json={"alpha": 0.2})
        assert pareto_response.status_code == 200
        assert pareto_response.json()["pareto_alpha"] == 0.2

        policy_response = client.post(
            "/api/agent/policy",
            json={"message": "Prioritize carbon zero mode"},
        )
        assert policy_response.status_code == 200
        assert policy_response.json()["tier"] == 1


def test_write_routes_require_operator_key_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_access_token", "test-operator-key")

    with TestClient(app) as client:
        assert client.get("/api/twin/state").status_code == 200
        assert client.get("/api/auth/check").status_code == 401

        denied = client.post("/api/optimizer/pareto", json={"alpha": 0.3})
        assert denied.status_code == 401

        allowed = client.post(
            "/api/optimizer/pareto",
            json={"alpha": 0.3},
            headers={"Authorization": "Bearer test-operator-key"},
        )
        assert allowed.status_code == 200

        check = client.get(
            "/api/auth/check",
            headers={"Authorization": "Bearer test-operator-key"},
        )
        assert check.status_code == 200
        assert check.json() == {"authenticated": True}


def test_invalid_request_body_is_rejected():
    with TestClient(app) as client:
        response = client.post("/api/optimizer/pareto", json={"alpha": 1.5})
        assert response.status_code == 422
