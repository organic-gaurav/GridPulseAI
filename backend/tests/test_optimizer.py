from app.services.optimizer import optimizer
from app.services.digital_twin import DualDigitalTwin


def test_optimizer_power_balance_and_bounds():
    twin = DualDigitalTwin()
    pv = [0.0] * 6 + [10.0, 25.0, 42.0, 52.0, 58.0, 60.0, 55.0, 45.0, 30.0, 15.0, 5.0] + [0.0] * 7
    res = optimizer.solve(
        pv_kw=pv,
        outdoor_temp_c=twin.outdoor_temp_c,
        carbon_intensity=twin.carbon_intensity,
        tariff_usd_kwh=twin.tariff_usd_kwh,
        base_load_kw=twin.base_load_kw,
        zones=twin.zones,
        ev_chargers=twin.ev_chargers,
        alpha=0.5,
    )
    assert res["status"] == "Optimal"
    assert res["solve_ms"] < 1500
    assert len(res["schedule"]) == 24
    for row in res["schedule"]:
        assert 15.0 <= row["battery_soc_pct"] <= 95.0
        assert row["grid_import_kw"] >= 0.0
        lhs = row["pv_kw"] + row["battery_discharge_kw"] + row["grid_import_kw"]
        rhs = row["base_load_kw"] + row["hvac_kw"] + row["ev_kw"] + row["deferrable_kw"] + row["battery_charge_kw"]
        assert lhs >= rhs - 0.1  # >= allows curtailment
