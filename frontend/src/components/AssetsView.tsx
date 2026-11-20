import { Battery, Car, Thermometer } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

export function AssetsView({ snapshot }: { snapshot: TwinSnapshot }) {
  return (
    <div className="space-y-4">
      <section aria-labelledby="thermal-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Thermometer aria-hidden="true" focusable="false" className="h-5 w-5 text-emerald-300" />
          <h2 id="thermal-heading" className="text-base font-semibold text-white">HVAC Thermal Zones (RC Balance, COP 3.2)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {snapshot.zones.map((z) => (
            <article key={z.zone_id} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-bold text-white">{z.zone_id} · {z.name}</h3>
                <span className={`text-xs px-2 py-1 rounded-full ${z.occupied ? "bg-emerald-500/20 text-emerald-200" : "bg-slate-800 text-slate-200"}`}>
                  {z.occupied ? "Occupied" : "Unoccupied"}
                </span>
              </div>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-2xl font-bold tabular-nums text-cyan-200">{z.temp_c.toFixed(1)}°C</p>
                <p className="text-sm text-slate-300 tabular-nums">Comfort band: {z.t_min.toFixed(1)}–{z.t_max.toFixed(1)}°C</p>
              </div>
              <div className="text-sm text-slate-300 tabular-nums flex flex-wrap justify-between gap-2 pt-2 border-t border-slate-800">
                <span>Optimized HVAC: {z.hvac_kw.toFixed(1)} kW</span>
                <span>Baseline: {z.base_hvac_kw.toFixed(1)} kW</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="ev-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Car aria-hidden="true" focusable="false" className="h-5 w-5 text-violet-300" />
          <h2 id="ev-heading" className="text-base font-semibold text-white">Smart EV Fleet Chargers (11 kW Max Each)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {snapshot.ev_chargers.map((ev) => {
            const pct = Math.min(100, Math.max(0, Math.round((ev.current_kwh / ev.target_kwh) * 100)));
            return (
              <article key={ev.charger_id} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-bold text-white">{ev.charger_id} · {ev.name}</h3>
                  <span className="text-xs text-violet-100 bg-violet-500/20 px-2 py-1 rounded-full">
                    Departs {String(ev.departure_hour).padStart(2, "0")}:00
                  </span>
                </div>
                <div
                  className="w-full bg-slate-700 h-3 rounded-full overflow-hidden"
                  role="progressbar"
                  aria-label={`${ev.name} battery charge`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={pct}
                  aria-valuetext={`${pct} percent charged, ${ev.current_kwh.toFixed(1)} of ${ev.target_kwh.toFixed(1)} kilowatt-hours`}
                >
                  <div aria-hidden="true" className="bg-violet-400 h-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <div className="flex flex-wrap justify-between gap-2 text-sm text-slate-300 tabular-nums">
                  <span>{ev.current_kwh.toFixed(1)} / {ev.target_kwh.toFixed(1)} kWh ({pct}%)</span>
                  <span>Arrives {String(ev.arrival_hour).padStart(2, "0")}:00</span>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="battery-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Battery aria-hidden="true" focusable="false" className="h-6 w-6 text-cyan-300" />
          <div>
            <h2 id="battery-heading" className="text-base font-semibold text-white">Stationary BESS (120 kWh / 40 kW)</h2>
            <p className="text-sm text-slate-300">Strict SoC guardrail: 15%–95% · 92% round-trip efficiency</p>
          </div>
        </div>
        <div className="text-left sm:text-right">
          <p className="text-2xl font-bold tabular-nums text-cyan-200">{snapshot.battery_soc_pct.toFixed(1)}%</p>
          <p className="text-sm text-slate-300 tabular-nums">
            {((snapshot.battery_soc_pct / 100) * snapshot.battery_capacity_kwh).toFixed(1)} kWh stored
          </p>
        </div>
      </section>
    </div>
  );
}
