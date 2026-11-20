from app.services.digital_twin import DualDigitalTwin


def test_dual_twin_divergence_and_chaos():
    twin = DualDigitalTwin()
    twin.reoptimize()
    for _ in range(5):
        twin.step_hour()
    snap = twin.get_snapshot()
    assert snap.base_total_cost_usd >= snap.opt_total_cost_usd
    assert snap.cost_saved_usd >= 0.0

    twin.inject_chaos("heatwave")
    assert "heatwave" in twin.active_chaos
    twin.inject_chaos("reset")
    assert twin.active_chaos == []
