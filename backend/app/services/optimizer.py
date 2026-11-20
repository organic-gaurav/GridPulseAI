import time
from typing import Dict, List
import pulp


class MicrogridOptimizer:
    """Deterministic 24-hour LP optimizer for the commercial building microgrid."""

    BATTERY_CAPACITY_KWH = 120.0
    BATTERY_MAX_KW = 40.0
    BATTERY_EFF = 0.959  # sqrt(0.92) ~ 0.959 one-way efficiency
    COP = 3.2
    PEAK_THRESHOLD_KW = 55.0
    PEAK_PENALTY_USD_PER_KW = 1.85
    BATTERY_WEAR_USD_PER_KWH = 0.015
    CARBON_WEIGHT_USD_PER_KG = 0.25  # Normalizes carbon cost to comparable USD scale

    def solve(
        self,
        pv_kw: List[float],
        outdoor_temp_c: List[float],
        carbon_intensity: List[float],
        tariff_usd_kwh: List[float],
        base_load_kw: List[float],
        zones: List[Dict],
        ev_chargers: List[Dict],
        alpha: float = 0.5,
        initial_soc_kwh: float = 60.0,
        min_soc_pct: float = 15.0,
        shed_deferrable: bool = False,
    ) -> Dict:
        t0 = time.perf_counter()
        hours = list(range(24))
        prob = pulp.LpProblem("GridPulse_24h_Dispatch", pulp.LpMinimize)

        # Decision variables
        grid_import = {h: pulp.LpVariable(f"grid_import_{h}", lowBound=0, upBound=250) for h in hours}
        curtail = {h: pulp.LpVariable(f"curtail_{h}", lowBound=0, upBound=100) for h in hours}
        b_chg = {h: pulp.LpVariable(f"b_chg_{h}", lowBound=0, upBound=self.BATTERY_MAX_KW) for h in hours}
        b_dis = {h: pulp.LpVariable(f"b_dis_{h}", lowBound=0, upBound=self.BATTERY_MAX_KW) for h in hours}
        b_soc = {
            h: pulp.LpVariable(
                f"b_soc_{h}",
                lowBound=self.BATTERY_CAPACITY_KWH * (min_soc_pct / 100.0),
                upBound=self.BATTERY_CAPACITY_KWH * 0.95,
            )
            for h in range(25)
        }
        peak_excess = pulp.LpVariable("peak_excess", lowBound=0, upBound=250)

        deferrable = {h: pulp.LpVariable(f"deferrable_{h}", lowBound=0, upBound=12.0) for h in hours}

        # EV variables
        ev_vars = {}
        for ev in ev_chargers:
            eid = ev["charger_id"]
            ev_vars[eid] = {h: pulp.LpVariable(f"ev_{eid}_{h}", lowBound=0, upBound=11.0) for h in hours}

        # HVAC variables & thermal RC state
        hvac_vars = {}
        temp_vars = {}
        slack_vars = {}
        for z in zones:
            zid = z["zone_id"]
            hvac_vars[zid] = {h: pulp.LpVariable(f"hvac_{zid}_{h}", lowBound=0, upBound=18.0) for h in hours}
            temp_vars[zid] = {h: pulp.LpVariable(f"temp_{zid}_{h}", lowBound=14.0, upBound=34.0) for h in range(25)}
            slack_vars[zid] = {h: pulp.LpVariable(f"slack_{zid}_{h}", lowBound=0, upBound=10.0) for h in hours}

        # Initial battery SoC
        prob += b_soc[0] == max(
            self.BATTERY_CAPACITY_KWH * (min_soc_pct / 100.0),
            min(self.BATTERY_CAPACITY_KWH * 0.95, initial_soc_kwh),
        )

        # Battery SoC transitions
        for h in hours:
            prob += (
                b_soc[h + 1]
                == b_soc[h] + self.BATTERY_EFF * b_chg[h] - (1.0 / self.BATTERY_EFF) * b_dis[h]
            )
            prob += b_chg[h] + b_dis[h] <= self.BATTERY_MAX_KW

        # Deferrable load target (24 kWh/day unless shed)
        deferrable_target = 0.0 if shed_deferrable else 24.0
        prob += pulp.lpSum([deferrable[h] for h in hours]) == deferrable_target

        # EV constraints
        for ev in ev_chargers:
            eid = ev["charger_id"]
            arr = int(ev["arrival_hour"])
            dep = int(ev["departure_hour"])
            needed = max(0.0, float(ev["target_kwh"]) - float(ev["current_kwh"]))
            active_hours = [h for h in hours if arr <= h < dep]
            max_possible = len(active_hours) * 11.0
            actual_target = min(needed, max_possible)
            for h in hours:
                if h not in active_hours:
                    prob += ev_vars[eid][h] == 0.0
            if active_hours:
                prob += pulp.lpSum([ev_vars[eid][h] for h in active_hours]) == actual_target

        # HVAC RC thermal constraints
        for z in zones:
            zid = z["zone_id"]
            prob += temp_vars[zid][0] == float(z["temp_c"])
            t_min = float(z["t_min"])
            t_max = float(z["t_max"])
            r_val = 6.5  # Thermal resistance factor
            c_gain = 0.22  # Cooling sensitivity (°C per kW-thermal)
            for h in hours:
                occ = 1.0 if (8 <= h <= 18) else 0.2
                q_int = 0.55 * occ
                prob += (
                    temp_vars[zid][h + 1]
                    == temp_vars[zid][h]
                    + (outdoor_temp_c[h] - temp_vars[zid][h]) / r_val
                    + q_int
                    - self.COP * hvac_vars[zid][h] * c_gain
                )
                prob += temp_vars[zid][h + 1] >= t_min - slack_vars[zid][h]
                prob += temp_vars[zid][h + 1] <= t_max + slack_vars[zid][h]

        # Power balance & peak demand at every hour
        for h in hours:
            hvac_sum = pulp.lpSum([hvac_vars[z["zone_id"]][h] for z in zones])
            ev_sum = pulp.lpSum([ev_vars[ev["charger_id"]][h] for ev in ev_chargers])
            prob += (
                pv_kw[h] + b_dis[h] + grid_import[h]
                == base_load_kw[h] + hvac_sum + ev_sum + deferrable[h] + b_chg[h] + curtail[h]
            )
            prob += grid_import[h] - self.PEAK_THRESHOLD_KW <= peak_excess

        # Objective function: Pareto combination of Cost and Carbon
        cost_term = (
            pulp.lpSum([grid_import[h] * tariff_usd_kwh[h] for h in hours])
            + peak_excess * self.PEAK_PENALTY_USD_PER_KW
            + pulp.lpSum([(b_chg[h] + b_dis[h]) * self.BATTERY_WEAR_USD_PER_KWH for h in hours])
        )
        carbon_term = pulp.lpSum(
            [grid_import[h] * (carbon_intensity[h] / 1000.0) * self.CARBON_WEIGHT_USD_PER_KG for h in hours]
        )
        slack_penalty = 1000.0 * pulp.lpSum(
            [slack_vars[z["zone_id"]][h] for z in zones for h in hours]
        )

        prob += alpha * cost_term + (1.0 - alpha) * carbon_term + slack_penalty

        # Solve silently with CBC
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        solve_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        schedule = []
        for h in hours:
            hvac_h = sum(pulp.value(hvac_vars[z["zone_id"]][h]) or 0.0 for z in zones)
            ev_h = sum(pulp.value(ev_vars[ev["charger_id"]][h]) or 0.0 for ev in ev_chargers)
            soc_pct = ((pulp.value(b_soc[h + 1]) or 0.0) / self.BATTERY_CAPACITY_KWH) * 100.0
            schedule.append(
                {
                    "hour": h,
                    "pv_kw": round(pv_kw[h], 2),
                    "base_load_kw": round(base_load_kw[h], 2),
                    "hvac_kw": round(hvac_h, 2),
                    "ev_kw": round(ev_h, 2),
                    "deferrable_kw": round(pulp.value(deferrable[h]) or 0.0, 2),
                    "battery_charge_kw": round(pulp.value(b_chg[h]) or 0.0, 2),
                    "battery_discharge_kw": round(pulp.value(b_dis[h]) or 0.0, 2),
                    "battery_soc_pct": round(soc_pct, 1),
                    "grid_import_kw": round(pulp.value(grid_import[h]) or 0.0, 2),
                    "hvac_by_zone": {
                        z["zone_id"]: round(pulp.value(hvac_vars[z["zone_id"]][h]) or 0.0, 2)
                        for z in zones
                    },
                    "ev_by_charger": {
                        ev["charger_id"]: round(pulp.value(ev_vars[ev["charger_id"]][h]) or 0.0, 2)
                        for ev in ev_chargers
                    },
                }
            )

        return {
            "status": pulp.LpStatus[prob.status],
            "solve_ms": solve_ms,
            "schedule": schedule,
        }


optimizer = MicrogridOptimizer()
