import math
from typing import Dict, List
from app.config import settings
from app.models.schemas import (
    ConstraintPatch,
    EVChargerState,
    FeedStatus,
    HourlySchedulePoint,
    TwinSnapshot,
    ZoneState,
)
from app.services.optimizer import optimizer


class DualDigitalTwin:
    """Physics-based Dual Digital Twin: Optimized Building vs. Unoptimized Baseline Building."""

    PV_PEAK_KW = 60.0
    BATTERY_CAPACITY_KWH = 120.0
    COP = 3.2

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.sim_hour: int = 8  # Start at 08:00 AM for rich daytime demo
        self.is_running: bool = False
        self.tick_seconds: float = settings.sim_tick_seconds
        self.pareto_alpha: float = 0.5
        self.min_soc_pct: float = 15.0
        self.shed_deferrable: bool = False
        self.active_chaos: List[str] = []

        self.weather_source: str = "Initializing..."
        self.carbon_source: str = "Initializing..."
        self.last_updated: str = "--:--:--"

        # 24h external profiles
        self.outdoor_temp_c: List[float] = [20.0] * 24
        self.irradiance_wm2: List[float] = [0.0] * 24
        self.carbon_intensity: List[float] = [200.0] * 24

        # Dynamic Time-of-Use Tariff ($/kWh): Off-peak $0.11, Mid $0.19, On-peak (16-21) $0.34
        self.tariff_usd_kwh: List[float] = [
            0.11 if (h < 7 or h >= 22) else (0.34 if 16 <= h <= 21 else 0.19)
            for h in range(24)
        ]
        # Commercial building baseload (lighting + IT/plugs)
        self.base_load_kw: List[float] = [
            round(16.0 + (14.0 if 8 <= h <= 18 else 2.0) + 2.0 * math.sin(h * math.pi / 12), 1)
            for h in range(24)
        ]

        # Battery state
        self.battery_soc_kwh: float = 60.0  # 50%

        # 3 HVAC Thermal Zones
        self.zones: List[Dict] = [
            {
                "zone_id": "Zone A",
                "name": "Open Office",
                "temp_c": 22.5,
                "t_min": 20.5,
                "t_max": 24.0,
                "occupied": True,
                "hvac_kw": 3.5,
                "base_temp_c": 22.0,
                "base_hvac_kw": 5.0,
            },
            {
                "zone_id": "Zone B",
                "name": "Conference & Exec",
                "temp_c": 22.0,
                "t_min": 20.5,
                "t_max": 24.0,
                "occupied": True,
                "hvac_kw": 2.5,
                "base_temp_c": 21.8,
                "base_hvac_kw": 4.2,
            },
            {
                "zone_id": "Zone C",
                "name": "Server & Lab Support",
                "temp_c": 20.0,
                "t_min": 18.0,
                "t_max": 22.5,
                "occupied": True,
                "hvac_kw": 4.5,
                "base_temp_c": 20.0,
                "base_hvac_kw": 5.5,
            },
        ]

        # 3 Smart EV Chargers
        self.ev_chargers: List[Dict] = [
            {
                "charger_id": "EV-1",
                "name": "Fleet Van #1",
                "connected": True,
                "arrival_hour": 8,
                "departure_hour": 17,
                "current_kwh": 12.0,
                "target_kwh": 52.0,
                "charge_kw": 0.0,
                "base_current_kwh": 12.0,
                "base_charge_kw": 11.0,
            },
            {
                "charger_id": "EV-2",
                "name": "Executive Sedan",
                "connected": True,
                "arrival_hour": 9,
                "departure_hour": 16,
                "current_kwh": 18.0,
                "target_kwh": 46.0,
                "charge_kw": 0.0,
                "base_current_kwh": 18.0,
                "base_charge_kw": 11.0,
            },
            {
                "charger_id": "EV-3",
                "name": "Service Shuttle",
                "connected": True,
                "arrival_hour": 10,
                "departure_hour": 19,
                "current_kwh": 10.0,
                "target_kwh": 54.0,
                "charge_kw": 0.0,
                "base_current_kwh": 10.0,
                "base_charge_kw": 11.0,
            },
        ]

        # Cumulative KPIs
        self.opt_total_cost_usd: float = 0.0
        self.base_total_cost_usd: float = 0.0
        self.opt_total_carbon_kg: float = 0.0
        self.base_total_carbon_kg: float = 0.0
        self.opt_peak_kw: float = 0.0
        self.base_peak_kw: float = 0.0
        self.total_pv_kwh: float = 0.0
        self.total_pv_used_kwh: float = 0.0

        self.schedule_24h: List[HourlySchedulePoint] = []
        self.last_solve_ms: float = 0.0

    def update_external_forecasts(self, data: Dict) -> None:
        self.outdoor_temp_c = list(data["outdoor_temp_c"])
        self.irradiance_wm2 = list(data["irradiance_wm2"])
        self.carbon_intensity = list(data["carbon_intensity"])
        self.weather_source = data["weather_source"]
        self.carbon_source = data["carbon_source"]
        self.last_updated = data["last_updated"]
        self._apply_chaos_modifiers()
        self.reoptimize()

    def _apply_chaos_modifiers(self) -> None:
        if "heatwave" in self.active_chaos:
            self.outdoor_temp_c = [round(t + 7.0, 1) for t in self.outdoor_temp_c]
        if "cloudburst" in self.active_chaos:
            self.irradiance_wm2 = [round(r * 0.35, 1) for r in self.irradiance_wm2]
        if "carbon_spike" in self.active_chaos:
            self.carbon_intensity = [round(c + 250.0, 1) for c in self.carbon_intensity]

    def compute_pv_profile(self) -> List[float]:
        pv = []
        for h in range(24):
            irr = self.irradiance_wm2[h]
            temp_derate = max(0.75, 1.0 - max(0.0, self.outdoor_temp_c[h] - 25.0) * 0.004)
            kw = self.PV_PEAK_KW * (irr / 1000.0) * temp_derate
            pv.append(round(min(self.PV_PEAK_KW, max(0.0, kw)), 2))
        return pv

    def compute_baseline_hour(self, h: int, pv_kw: float) -> Dict:
        """Unoptimized Baseline: naive thermostat + immediate EV charging + no battery."""
        hvac_base = 0.0
        for z in self.zones:
            # Naive setpoint 21.5°C
            diff = self.outdoor_temp_c[h] - 21.5
            kw = max(1.5, min(16.0, 3.2 + max(0.0, diff) * 0.65))
            if "hvac_fault" in self.active_chaos and z["zone_id"] == "Zone A":
                kw += 14.0
            z["base_hvac_kw"] = round(kw, 2)
            hvac_base += kw

        ev_base = 0.0
        for ev in self.ev_chargers:
            if ev["arrival_hour"] <= h < ev["departure_hour"] and ev["base_current_kwh"] < ev["target_kwh"]:
                chg = min(11.0, ev["target_kwh"] - ev["base_current_kwh"])
                ev["base_charge_kw"] = round(chg, 2)
                ev_base += chg
            else:
                ev["base_charge_kw"] = 0.0

        def_base = 8.0 if h in (17, 18, 19) else 0.0  # Unfortunate peak-hour batch
        total_load = self.base_load_kw[h] + hvac_base + ev_base + def_base
        grid_import = max(0.0, total_load - pv_kw)
        return {
            "grid_import_kw": round(grid_import, 2),
            "hvac_kw": round(hvac_base, 2),
            "ev_kw": round(ev_base, 2),
        }

    def reoptimize(self) -> None:
        pv_profile = self.compute_pv_profile()
        result = optimizer.solve(
            pv_kw=pv_profile,
            outdoor_temp_c=self.outdoor_temp_c,
            carbon_intensity=self.carbon_intensity,
            tariff_usd_kwh=self.tariff_usd_kwh,
            base_load_kw=self.base_load_kw,
            zones=self.zones,
            ev_chargers=self.ev_chargers,
            alpha=self.pareto_alpha,
            initial_soc_kwh=self.battery_soc_kwh,
            min_soc_pct=self.min_soc_pct,
            shed_deferrable=self.shed_deferrable,
        )
        self.last_solve_ms = result["solve_ms"]

        new_schedule: List[HourlySchedulePoint] = []
        for row in result["schedule"]:
            h = row["hour"]
            base_h = self.compute_baseline_hour(h, pv_profile[h])
            new_schedule.append(
                HourlySchedulePoint(
                    hour=h,
                    label=f"{h:02d}:00",
                    pv_kw=row["pv_kw"],
                    base_load_kw=row["base_load_kw"],
                    hvac_kw=row["hvac_kw"],
                    ev_kw=row["ev_kw"],
                    deferrable_kw=row["deferrable_kw"],
                    battery_charge_kw=row["battery_charge_kw"],
                    battery_discharge_kw=row["battery_discharge_kw"],
                    battery_soc_pct=row["battery_soc_pct"],
                    grid_import_kw=row["grid_import_kw"],
                    base_grid_import_kw=base_h["grid_import_kw"],
                    carbon_intensity=self.carbon_intensity[h],
                    tariff_usd_kwh=self.tariff_usd_kwh[h],
                    outdoor_temp_c=self.outdoor_temp_c[h],
                )
            )
        self.schedule_24h = new_schedule

    def step_hour(self) -> Dict:
        """Advance simulation by 1 hour and update both Optimized and Baseline twins."""
        h = self.sim_hour
        if not self.schedule_24h:
            self.reoptimize()

        pt = self.schedule_24h[h]
        base_h = self.compute_baseline_hour(h, pt.pv_kw)

        # Update battery SoC
        self.battery_soc_kwh = (pt.battery_soc_pct / 100.0) * self.BATTERY_CAPACITY_KWH

        # Update EV states
        for ev in self.ev_chargers:
            if ev["arrival_hour"] <= h < ev["departure_hour"]:
                ev["current_kwh"] = round(min(ev["target_kwh"], ev["current_kwh"] + pt.ev_kw / 3.0), 2)
                ev["base_current_kwh"] = round(
                    min(ev["target_kwh"], ev["base_current_kwh"] + base_h["ev_kw"] / 3.0), 2
                )

        # Update HVAC zone temperatures
        for z in self.zones:
            z["occupied"] = 8 <= h <= 18
            fault_kw = 14.0 if ("hvac_fault" in self.active_chaos and z["zone_id"] == "Zone A") else 0.0
            z["hvac_kw"] = round(pt.hvac_kw / 3.0 + fault_kw, 2)
            z["temp_c"] = round(
                max(z["t_min"], min(z["t_max"], z["temp_c"] + (self.outdoor_temp_c[h] - z["temp_c"]) * 0.1 - 0.15)),
                1,
            )

        # Update cumulative KPIs
        opt_grid = pt.grid_import_kw + (14.0 if "hvac_fault" in self.active_chaos else 0.0)
        base_grid = base_h["grid_import_kw"]
        tariff = self.tariff_usd_kwh[h]
        carbon_g = self.carbon_intensity[h]

        opt_cost = opt_grid * tariff
        base_cost = base_grid * tariff
        opt_carb = (opt_grid * carbon_g) / 1000.0
        base_carb = (base_grid * carbon_g) / 1000.0

        self.opt_total_cost_usd = round(self.opt_total_cost_usd + opt_cost, 2)
        self.base_total_cost_usd = round(self.base_total_cost_usd + base_cost, 2)
        self.opt_total_carbon_kg = round(self.opt_total_carbon_kg + opt_carb, 2)
        self.base_total_carbon_kg = round(self.base_total_carbon_kg + base_carb, 2)
        self.opt_peak_kw = round(max(self.opt_peak_kw, opt_grid), 2)
        self.base_peak_kw = round(max(self.base_peak_kw, base_grid), 2)

        self.total_pv_kwh += pt.pv_kw
        self.total_pv_used_kwh += min(pt.pv_kw, pt.base_load_kw + pt.hvac_kw + pt.ev_kw + pt.battery_charge_kw)

        self.sim_hour = (self.sim_hour + 1) % 24
        if self.sim_hour == 0:
            # Reset daily EVs for next cycle
            for ev in self.ev_chargers:
                ev["current_kwh"] = 10.0
                ev["base_current_kwh"] = 10.0

        return {
            "sim_hour": h,
            "opt_grid_kw": opt_grid,
            "base_grid_kw": base_grid,
            "pv_kw": pt.pv_kw,
            "battery_soc_pct": pt.battery_soc_pct,
            "opt_cost_usd": round(opt_cost, 2),
            "base_cost_usd": round(base_cost, 2),
            "opt_carbon_kg": round(opt_carb, 2),
            "base_carbon_kg": round(base_carb, 2),
            "carbon_intensity": carbon_g,
            "tariff_usd_kwh": tariff,
        }

    def inject_chaos(self, event: str) -> None:
        if event == "reset":
            self.active_chaos = []
            self.reoptimize()
            return
        if event not in self.active_chaos:
            self.active_chaos.append(event)
        if event == "urgent_ev":
            self.ev_chargers[0]["target_kwh"] = min(65.0, self.ev_chargers[0]["current_kwh"] + 45.0)
            self.ev_chargers[0]["departure_hour"] = min(23, self.sim_hour + 4)
        self._apply_chaos_modifiers()
        self.reoptimize()

    def apply_constraint_patch(self, patch: ConstraintPatch) -> None:
        if patch.zone_temp_overrides:
            for zone in self.zones:
                override = patch.zone_temp_overrides.get(zone["zone_id"])
                if override is None:
                    continue
                if override.t_min is not None:
                    zone["t_min"] = override.t_min
                if override.t_max is not None:
                    zone["t_max"] = override.t_max

        if patch.ev_target_overrides:
            for charger in self.ev_chargers:
                override = patch.ev_target_overrides.get(charger["charger_id"])
                if override is None:
                    continue
                if override.departure_hour is not None:
                    charger["departure_hour"] = override.departure_hour
                if override.target_kwh is not None:
                    charger["target_kwh"] = override.target_kwh
        if patch.battery_min_soc_pct is not None:
            self.min_soc_pct = patch.battery_min_soc_pct
        if patch.pareto_alpha is not None:
            self.pareto_alpha = patch.pareto_alpha
        if patch.shed_deferrable is not None:
            self.shed_deferrable = patch.shed_deferrable
        self.reoptimize()

    def get_snapshot(self) -> TwinSnapshot:
        if not self.schedule_24h:
            self.reoptimize()
        pt = self.schedule_24h[self.sim_hour]
        cost_saved = round(max(0.0, self.base_total_cost_usd - self.opt_total_cost_usd), 2)
        cost_pct = round((cost_saved / self.base_total_cost_usd * 100.0), 1) if self.base_total_cost_usd > 0 else 0.0
        carb_saved = round(max(0.0, self.base_total_carbon_kg - self.opt_total_carbon_kg), 2)
        carb_pct = round((carb_saved / self.base_total_carbon_kg * 100.0), 1) if self.base_total_carbon_kg > 0 else 0.0
        peak_shaved = round(max(0.0, self.base_peak_kw - self.opt_peak_kw), 2)
        solar_self = round((self.total_pv_used_kwh / self.total_pv_kwh * 100.0), 1) if self.total_pv_kwh > 0 else 94.2

        return TwinSnapshot(
            sim_hour=self.sim_hour,
            is_running=self.is_running,
            tick_seconds=self.tick_seconds,
            pareto_alpha=self.pareto_alpha,
            active_chaos=self.active_chaos,
            feed_status=FeedStatus(
                weather_source=self.weather_source,
                carbon_source=self.carbon_source,
                ai_mode=settings.ai_mode,
                last_updated=self.last_updated,
            ),
            pv_kw=pt.pv_kw,
            grid_import_kw=pt.grid_import_kw,
            base_grid_import_kw=pt.base_grid_import_kw,
            battery_power_kw=round(pt.battery_discharge_kw - pt.battery_charge_kw, 2),
            battery_soc_pct=pt.battery_soc_pct,
            battery_capacity_kwh=self.BATTERY_CAPACITY_KWH,
            hvac_total_kw=pt.hvac_kw,
            ev_total_kw=pt.ev_kw,
            base_load_kw=pt.base_load_kw,
            deferrable_kw=pt.deferrable_kw,
            outdoor_temp_c=pt.outdoor_temp_c,
            carbon_intensity=pt.carbon_intensity,
            tariff_usd_kwh=pt.tariff_usd_kwh,
            opt_total_cost_usd=self.opt_total_cost_usd,
            base_total_cost_usd=self.base_total_cost_usd,
            cost_saved_usd=cost_saved,
            cost_saved_pct=cost_pct,
            opt_total_carbon_kg=self.opt_total_carbon_kg,
            base_total_carbon_kg=self.base_total_carbon_kg,
            carbon_avoided_kg=carb_saved,
            carbon_avoided_pct=carb_pct,
            opt_peak_kw=self.opt_peak_kw,
            base_peak_kw=self.base_peak_kw,
            peak_shaved_kw=peak_shaved,
            solar_self_consumption_pct=solar_self,
            zones=[ZoneState(**z) for z in self.zones],
            ev_chargers=[EVChargerState(**ev) for ev in self.ev_chargers],
            schedule_24h=self.schedule_24h,
        )


twin = DualDigitalTwin()
