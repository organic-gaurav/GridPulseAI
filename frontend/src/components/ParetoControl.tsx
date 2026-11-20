import { Sliders } from "lucide-react";

interface Props {
  alpha: number;
  onChange: (alpha: number) => void;
}

export function ParetoControl({ alpha, onChange }: Props) {
  const modeLabel =
    alpha <= 0.25 ? "Carbon-Zero Priority" : alpha >= 0.75 ? "Cost-First Priority" : "Balanced Pareto";

  return (
    <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sliders className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Cost-vs.-Carbon Pareto Frontier</h3>
        </div>
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300 border border-slate-700">
          {modeLabel} (α = {alpha.toFixed(2)})
        </span>
      </div>

      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={alpha}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-cyan-400 cursor-pointer"
      />

      <div className="flex justify-between text-[11px] text-slate-400 mt-1">
        <span className="text-emerald-400 font-medium">0.0 • Carbon-Zero</span>
        <span>0.5 • Balanced</span>
        <span className="text-amber-400 font-medium">1.0 • Cost-First</span>
      </div>
    </div>
  );
}
