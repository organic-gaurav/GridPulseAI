import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TwinSnapshot } from "../types/grid";

export function DispatchChart({ snapshot }: { snapshot: TwinSnapshot }) {
  const [showBaseline, setShowBaseline] = useState(true);

  return (
    <section aria-labelledby="dispatch-chart-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div>
          <h2 id="dispatch-chart-heading" className="text-base font-semibold text-white">
            24-Hour Optimal Dispatch &amp; Grid Carbon
          </h2>
          <p id="dispatch-chart-description" className="text-sm text-slate-300 mt-1">
            Deterministic linear-programming schedule compared with the unoptimized baseline.
            Use the chart legend to identify solar generation, optimized grid import, baseline
            grid import, and carbon intensity.
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-200 cursor-pointer">
          <input
            type="checkbox"
            checked={showBaseline}
            onChange={(e) => setShowBaseline(e.target.checked)}
            className="accent-rose-400 rounded"
          />
          Overlay Baseline Grid Load
        </label>
      </div>

      <figure aria-labelledby="dispatch-chart-heading" aria-describedby="dispatch-chart-description">
        <div className="h-72 w-full" role="group" aria-label="Interactive 24-hour dispatch chart. Use arrow keys to navigate plotted data points.">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              accessibilityLayer
              data={snapshot.schedule_24h}
              margin={{ top: 8, right: 14, left: 0, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="label" tick={{ fill: "#CBD5E1", fontSize: 12 }} interval={2} />
              <YAxis yAxisId="kw" tick={{ fill: "#CBD5E1", fontSize: 12 }} unit="kW" width={52} />
              <YAxis yAxisId="carb" orientation="right" tick={{ fill: "#CBD5E1", fontSize: 12 }} unit="g" width={46} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0F172A",
                  borderColor: "#64748B",
                  borderRadius: "8px",
                  color: "#F8FAFC",
                  fontSize: "13px",
                }}
                labelStyle={{ color: "#F8FAFC" }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", color: "#F1F5F9" }} />
              <Bar yAxisId="kw" dataKey="pv_kw" name="Solar PV (kW)" stackId="gen" fill="#F59E0B" radius={[2, 2, 0, 0]} />
              <Bar yAxisId="kw" dataKey="grid_import_kw" name="Optimized Grid (kW)" stackId="gen" fill="#06B6D4" radius={[2, 2, 0, 0]} />
              {showBaseline && (
                <Line
                  yAxisId="kw"
                  type="monotone"
                  dataKey="base_grid_import_kw"
                  name="Baseline Grid (kW)"
                  stroke="#FB7185"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              <Line
                yAxisId="carb"
                type="monotone"
                dataKey="carbon_intensity"
                name="Carbon (gCO₂/kWh)"
                stroke="#34D399"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <figcaption className="text-sm text-slate-300 mt-2">
          Chart values update with the live digital twin. The baseline overlay can be shown or hidden with the checkbox above.
        </figcaption>
      </figure>
    </section>
  );
}
