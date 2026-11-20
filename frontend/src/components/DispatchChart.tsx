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
    <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div>
          <h2 className="text-sm font-semibold text-white">24-Hour Optimal Dispatch & Grid Carbon</h2>
          <p className="text-[11px] text-slate-400">
            Deterministic LP schedule vs. Unoptimized Baseline
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={showBaseline}
            onChange={(e) => setShowBaseline(e.target.checked)}
            className="accent-rose-500 rounded"
          />
          Overlay Baseline Grid Load
        </label>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={snapshot.schedule_24h} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
            <XAxis dataKey="label" tick={{ fill: "#94A3B8", fontSize: 10 }} interval={2} />
            <YAxis yAxisId="kw" tick={{ fill: "#94A3B8", fontSize: 10 }} unit="kW" />
            <YAxis yAxisId="carb" orientation="right" tick={{ fill: "#94A3B8", fontSize: 10 }} unit="g" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0F172A",
                borderColor: "#334155",
                borderRadius: "8px",
                fontSize: "11px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "11px" }} />
            <Bar yAxisId="kw" dataKey="pv_kw" name="Solar PV (kW)" stackId="gen" fill="#F59E0B" radius={[2, 2, 0, 0]} />
            <Bar yAxisId="kw" dataKey="grid_import_kw" name="Optimized Grid (kW)" stackId="gen" fill="#06B6D4" radius={[2, 2, 0, 0]} />
            {showBaseline && (
              <Line
                yAxisId="kw"
                type="monotone"
                dataKey="base_grid_import_kw"
                name="Baseline Grid (kW)"
                stroke="#F43F5E"
                strokeWidth={2}
                dot={false}
              />
            )}
            <Line
              yAxisId="carb"
              type="monotone"
              dataKey="carbon_intensity"
              name="Carbon (gCO₂/kWh)"
              stroke="#10B981"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
