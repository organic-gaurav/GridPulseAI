import { DollarSign, Gauge, Leaf, Zap } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

export function KpiStrip({ snapshot }: { snapshot: TwinSnapshot }) {
  const cards = [
    {
      label: "Live Net Grid Load",
      value: `${snapshot.grid_import_kw.toFixed(1)} kW`,
      sub: `Baseline: ${snapshot.base_grid_import_kw.toFixed(1)} kW`,
      icon: Zap,
      color: "text-rose-400",
      bg: "bg-rose-500/10 border-rose-500/20",
    },
    {
      label: "Verified Cost Saved",
      value: `$${snapshot.cost_saved_usd.toFixed(2)}`,
      sub: `${snapshot.cost_saved_pct.toFixed(1)}% vs. Baseline`,
      icon: DollarSign,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/20",
    },
    {
      label: "Scope 2 CO₂ Avoided",
      value: `${snapshot.carbon_avoided_kg.toFixed(1)} kg`,
      sub: `${snapshot.carbon_avoided_pct.toFixed(1)}% reduction`,
      icon: Leaf,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10 border-cyan-500/20",
    },
    {
      label: "Peak Demand Shaved",
      value: `${snapshot.peak_shaved_kw.toFixed(1)} kW`,
      sub: `Solar Self-Use: ${snapshot.solar_self_consumption_pct.toFixed(0)}%`,
      icon: Gauge,
      color: "text-amber-400",
      bg: "bg-amber-500/10 border-amber-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.label}
            className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between"
          >
            <div>
              <p className="text-xs text-slate-400 font-medium">{c.label}</p>
              <p className="text-2xl font-bold tabular-nums text-white mt-1">{c.value}</p>
              <p className="text-[11px] text-slate-400 mt-0.5 tabular-nums">{c.sub}</p>
            </div>
            <div className={`h-10 w-10 rounded-lg border flex items-center justify-center ${c.bg}`}>
              <Icon className={`h-5 w-5 ${c.color}`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
