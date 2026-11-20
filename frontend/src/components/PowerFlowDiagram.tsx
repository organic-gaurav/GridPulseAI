import { BatteryCharging, Building2, Car, Sun, Zap } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

export function PowerFlowDiagram({ snapshot }: { snapshot: TwinSnapshot }) {
  const battDischarging = snapshot.battery_power_kw > 0.1;
  const battCharging = snapshot.battery_power_kw < -0.1;

  return (
    <section aria-labelledby="power-flow-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h2 id="power-flow-heading" className="text-base font-semibold text-white">Live Microgrid Power Flow</h2>
        <p className="text-sm text-slate-300 tabular-nums">
          Outdoor: {snapshot.outdoor_temp_c.toFixed(1)}°C · Tariff: ${snapshot.tariff_usd_kwh.toFixed(2)}/kWh · Carbon: {snapshot.carbon_intensity.toFixed(0)} gCO₂/kWh
        </p>
      </div>

      <figure aria-labelledby="power-flow-heading" aria-describedby="power-flow-description">
        <div className="relative w-full min-h-60 h-60 sm:h-64 flex items-center justify-center">
          <svg
            viewBox="0 0 600 210"
            aria-hidden="true"
            focusable="false"
            className="w-full h-full max-w-2xl"
          >
            <line x1="110" y1="45" x2="285" y2="105" stroke="#F59E0B" strokeWidth={snapshot.pv_kw > 0.5 ? 3 : 1.5} className={snapshot.pv_kw > 0.5 ? "animate-flow" : "opacity-50"} />
            <line x1="110" y1="165" x2="285" y2="105" stroke="#F43F5E" strokeWidth={snapshot.grid_import_kw > 0.5 ? 3 : 1.5} className={snapshot.grid_import_kw > 0.5 ? "animate-flow" : "opacity-50"} />
            <line x1="300" y1="105" x2="300" y2="180" stroke="#06B6D4" strokeWidth={battCharging || battDischarging ? 3 : 1.5} className={battCharging || battDischarging ? "animate-flow" : "opacity-50"} />
            <line x1="315" y1="105" x2="490" y2="45" stroke="#10B981" strokeWidth={2.5} className="animate-flow" />
            <line x1="315" y1="105" x2="490" y2="165" stroke="#8B5CF6" strokeWidth={snapshot.ev_total_kw > 0.5 ? 3 : 1.5} className={snapshot.ev_total_kw > 0.5 ? "animate-flow" : "opacity-50"} />
            <circle cx="300" cy="105" r="24" fill="#0F172A" stroke="#67E8F9" strokeWidth="2" />
            <text x="300" y="102" textAnchor="middle" fill="#F8FAFC" fontSize="9" fontWeight="700">AC BUS</text>
            <text x="300" y="114" textAnchor="middle" fill="#67E8F9" fontSize="8">{snapshot.base_load_kw.toFixed(0)}kW Base</text>
          </svg>

          <div className="absolute top-2 left-2 bg-slate-900 border border-amber-400/60 rounded-lg px-3 py-2 flex items-center gap-2">
            <Sun aria-hidden="true" focusable="false" className="h-5 w-5 text-amber-300" />
            <div>
              <p className="text-xs text-slate-200">Solar PV</p>
              <p className="text-sm font-bold tabular-nums text-amber-200">{snapshot.pv_kw.toFixed(1)} kW</p>
            </div>
          </div>

          <div className="absolute bottom-2 left-2 bg-slate-900 border border-rose-400/60 rounded-lg px-3 py-2 flex items-center gap-2">
            <Zap aria-hidden="true" focusable="false" className="h-5 w-5 text-rose-300" />
            <div>
              <p className="text-xs text-slate-200">Grid Import</p>
              <p className="text-sm font-bold tabular-nums text-rose-200">{snapshot.grid_import_kw.toFixed(1)} kW</p>
            </div>
          </div>

          <div className="absolute bottom-1 left-1/2 -translate-x-1/2 bg-slate-900 border border-cyan-400/60 rounded-lg px-3 py-2 flex items-center gap-2">
            <BatteryCharging aria-hidden="true" focusable="false" className="h-5 w-5 text-cyan-300" />
            <div>
              <p className="text-xs text-slate-200">Battery · {snapshot.battery_soc_pct.toFixed(0)}%</p>
              <p className="text-sm font-bold tabular-nums text-cyan-200">
                {snapshot.battery_power_kw > 0
                  ? `+${snapshot.battery_power_kw.toFixed(1)} kW discharging`
                  : snapshot.battery_power_kw < 0
                  ? `${Math.abs(snapshot.battery_power_kw).toFixed(1)} kW charging`
                  : "Idle"}
              </p>
            </div>
          </div>

          <div className="absolute top-2 right-2 bg-slate-900 border border-emerald-400/60 rounded-lg px-3 py-2 flex items-center gap-2">
            <Building2 aria-hidden="true" focusable="false" className="h-5 w-5 text-emerald-300" />
            <div>
              <p className="text-xs text-slate-200">HVAC · 3 zones</p>
              <p className="text-sm font-bold tabular-nums text-emerald-200">{snapshot.hvac_total_kw.toFixed(1)} kW</p>
            </div>
          </div>

          <div className="absolute bottom-2 right-2 bg-slate-900 border border-violet-400/60 rounded-lg px-3 py-2 flex items-center gap-2">
            <Car aria-hidden="true" focusable="false" className="h-5 w-5 text-violet-300" />
            <div>
              <p className="text-xs text-slate-200">EV Fleet · 3 vehicles</p>
              <p className="text-sm font-bold tabular-nums text-violet-200">{snapshot.ev_total_kw.toFixed(1)} kW</p>
            </div>
          </div>
        </div>
        <figcaption id="power-flow-description" className="text-sm text-slate-300 mt-3">
          Power-flow overview. Solar generation and grid import feed the AC bus; the bus supplies the HVAC zones and EV fleet and exchanges energy with the battery. Current values are shown for each source and load.
        </figcaption>
      </figure>
    </section>
  );
}
