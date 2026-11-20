import { Battery, Car, Thermometer } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

export function AssetsView({ snapshot }: { snapshot: TwinSnapshot }) {
  return (
    <div className="space-y-4">
      <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Thermometer className="h-4 w-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">HVAC Thermal Zones (RC Balance, COP 3.2)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {snapshot.zones.map((z) => (
            <div key={z.zone_id} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">
                  {z.zone_id} • {z.name}
                </span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    z.occupied ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {z.occupied ? "Occupied" : "Unoccupied"}
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold tabular-nums text-cyan-300">{z.temp_c.toFixed(1)}°C</span>
                <span className="text-xs text-slate-400 tabular-nums">
                  Band: {z.t_min.toFixed(1)}–{z.t_max.toFixed(1)}°C
                </span>
              </div>
              <div className="text-[11px] text-slate-400 tabular-nums flex justify-between pt-1 border-t border-slate-800">
                <span>Opt HVAC: {z.hvac_kw.toFixed(1)} kW</span>
                <span className="text-rose-400">Base: {z.base_hvac_kw.toFixed(1)} kW</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Car className="h-4 w-4 text-violet-400" />
          <h2 className="text-sm font-semibold text-white">Smart EV Fleet Chargers (11 kW Max Each)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {snapshot.ev_chargers.map((ev) => {
            const pct = Math.min(100, Math.round((ev.current_kwh / ev.target_kwh) * 100));
            return (
              <div key={ev.charger_id} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">
                    {ev.charger_id} • {ev.name}
                  </span>
                  <span className="text-[10px] text-violet-300 bg-violet-500/15 px-2 py-0.5 rounded-full">
                    Departs {String(ev.departure_hour).padStart(2, "0")}:00
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-violet-500 h-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <div className="flex justify-between text-[11px] text-slate-400 tabular-nums">
                  <span>
                    {ev.current_kwh.toFixed(1)} / {ev.target_kwh.toFixed(1)} kWh ({pct}%)
                  </span>
                  <span>Arr: {String(ev.arrival_hour).padStart(2, "0")}:00</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Battery className="h-5 w-5 text-cyan-400" />
          <div>
            <div className="text-sm font-semibold text-white">Stationary BESS (120 kWh / 40 kW)</div>
            <div className="text-xs text-slate-400">Strict SoC Guardrail: 15% – 95% • 92% Round-Trip Efficiency</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xl font-bold tabular-nums text-cyan-300">{snapshot.battery_soc_pct.toFixed(1)}%</div>
          <div className="text-xs text-slate-400 tabular-nums">
            {((snapshot.battery_soc_pct / 100) * snapshot.battery_capacity_kwh).toFixed(1)} kWh stored
          </div>
        </div>
      </div>
    </div>
  );
}
