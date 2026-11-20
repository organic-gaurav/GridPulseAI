import { BatteryCharging, Building2, Car, Sun, Zap } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

export function PowerFlowDiagram({ snapshot }: { snapshot: TwinSnapshot }) {
  const battDischarging = snapshot.battery_power_kw > 0.1;
  const battCharging = snapshot.battery_power_kw < -0.1;

  return (
    <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-white">Live Microgrid Power Flow</h2>
        <span className="text-xs text-slate-400 tabular-nums">
          Outdoor: {snapshot.outdoor_temp_c.toFixed(1)}°C • Tariff: ${snapshot.tariff_usd_kwh.toFixed(2)}/kWh • Carbon:{" "}
          {snapshot.carbon_intensity.toFixed(0)} gCO₂/kWh
        </span>
      </div>

      <div className="relative w-full h-56 flex items-center justify-center">
        <svg viewBox="0 0 600 210" className="w-full h-full max-w-2xl">
          {/* Animated Flow Lines */}
          {/* Solar -> Hub */}
          <line
            x1="110"
            y1="45"
            x2="285"
            y2="105"
            stroke="#F59E0B"
            strokeWidth={snapshot.pv_kw > 0.5 ? 3 : 1.5}
            className={snapshot.pv_kw > 0.5 ? "animate-flow" : "opacity-30"}
          />
          {/* Grid -> Hub */}
          <line
            x1="110"
            y1="165"
            x2="285"
            y2="105"
            stroke="#F43F5E"
            strokeWidth={snapshot.grid_import_kw > 0.5 ? 3 : 1.5}
            className={snapshot.grid_import_kw > 0.5 ? "animate-flow" : "opacity-30"}
          />
          {/* Hub <-> Battery */}
          <line
            x1="300"
            y1="105"
            x2="300"
            y2="180"
            stroke="#06B6D4"
            strokeWidth={battCharging || battDischarging ? 3 : 1.5}
            className={battCharging || battDischarging ? "animate-flow" : "opacity-30"}
          />
          {/* Hub -> HVAC */}
          <line
            x1="315"
            y1="105"
            x2="490"
            y2="45"
            stroke="#10B981"
            strokeWidth={2.5}
            className="animate-flow"
          />
          {/* Hub -> EV */}
          <line
            x1="315"
            y1="105"
            x2="490"
            y2="165"
            stroke="#8B5CF6"
            strokeWidth={snapshot.ev_total_kw > 0.5 ? 3 : 1.5}
            className={snapshot.ev_total_kw > 0.5 ? "animate-flow" : "opacity-30"}
          />

          {/* Center Microgrid Bus */}
          <circle cx="300" cy="105" r="24" fill="#0F172A" stroke="#38BDF8" strokeWidth="2" />
          <text x="300" y="102" textAnchor="middle" fill="#F8FAFC" fontSize="9" fontWeight="700">
            AC BUS
          </text>
          <text x="300" y="114" textAnchor="middle" fill="#38BDF8" fontSize="8">
            {snapshot.base_load_kw.toFixed(0)}kW Base
          </text>
        </svg>

        {/* Overlay Nodes */}
        <div className="absolute top-2 left-2 bg-slate-900/95 border border-amber-500/40 rounded-lg px-3 py-2 flex items-center gap-2">
          <Sun className="h-4 w-4 text-amber-400" />
          <div>
            <div className="text-[10px] text-slate-400">Solar PV</div>
            <div className="text-xs font-bold tabular-nums text-amber-300">{snapshot.pv_kw.toFixed(1)} kW</div>
          </div>
        </div>

        <div className="absolute bottom-2 left-2 bg-slate-900/95 border border-rose-500/40 rounded-lg px-3 py-2 flex items-center gap-2">
          <Zap className="h-4 w-4 text-rose-400" />
          <div>
            <div className="text-[10px] text-slate-400">Grid Import</div>
            <div className="text-xs font-bold tabular-nums text-rose-300">{snapshot.grid_import_kw.toFixed(1)} kW</div>
          </div>
        </div>

        <div className="absolute bottom-1 left-1/2 -translate-x-1/2 bg-slate-900/95 border border-cyan-500/40 rounded-lg px-3 py-1.5 flex items-center gap-2">
          <BatteryCharging className="h-4 w-4 text-cyan-400" />
          <div>
            <div className="text-[10px] text-slate-400">
              BESS ({snapshot.battery_soc_pct.toFixed(0)}%)
            </div>
            <div className="text-xs font-bold tabular-nums text-cyan-300">
              {snapshot.battery_power_kw > 0
                ? `+${snapshot.battery_power_kw.toFixed(1)} kW Dis`
                : snapshot.battery_power_kw < 0
                ? `${Math.abs(snapshot.battery_power_kw).toFixed(1)} kW Chg`
                : "Idle"}
            </div>
          </div>
        </div>

        <div className="absolute top-2 right-2 bg-slate-900/95 border border-emerald-500/40 rounded-lg px-3 py-2 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-emerald-400" />
          <div>
            <div className="text-[10px] text-slate-400">HVAC (3 Zones)</div>
            <div className="text-xs font-bold tabular-nums text-emerald-300">{snapshot.hvac_total_kw.toFixed(1)} kW</div>
          </div>
        </div>

        <div className="absolute bottom-2 right-2 bg-slate-900/95 border border-violet-500/40 rounded-lg px-3 py-2 flex items-center gap-2">
          <Car className="h-4 w-4 text-violet-400" />
          <div>
            <div className="text-[10px] text-slate-400">EV Fleet (3)</div>
            <div className="text-xs font-bold tabular-nums text-violet-300">{snapshot.ev_total_kw.toFixed(1)} kW</div>
          </div>
        </div>
      </div>
    </div>
  );
}
