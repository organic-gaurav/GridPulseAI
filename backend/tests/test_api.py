from fastapi.testclient import TestClient
from app.main import app


def test_api_endpoints():
    with TestClient(app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        r_state = client.get("/api/twin/state")
        assert r_state.status_code == 200
        data = r_state.json()
        assert "schedule_24h" in data
        assert len(data["schedule_24h"]) == 24

        r_pareto = client.post("/api/optimizer/pareto", json={"alpha": 0.2})
        assert r_pareto.status_code == 200
        assert r_pareto.json()["pareto_alpha"] == 0.2

        r_pol = client.post("/api/agent/policy", json={"message": "Prioritize carbon zero mode"})
        assert r_pol.status_code == 200
        assert r_pol.json()["tier"] == 1
