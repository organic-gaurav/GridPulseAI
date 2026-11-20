import { Sliders } from "lucide-react";

interface Props {
  alpha: number;
  operatorReady: boolean;
  onChange: (alpha: number) => void;
}

export function ParetoControl({ alpha, operatorReady, onChange }: Props) {
  const modeLabel =
    alpha <= 0.25 ? "Carbon-Zero Priority" : alpha >= 0.75 ? "Cost-First Priority" : "Balanced Pareto";

  return (
    <section aria-labelledby="pareto-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Sliders aria-hidden="true" focusable="false" className="h-4 w-4 text-cyan-300" />
          <h2 id="pareto-heading" className="text-sm font-semibold text-white">Cost-vs.-Carbon Pareto Frontier</h2>
        </div>
        <output
          htmlFor="pareto-alpha"
          aria-live="polite"
          className="text-sm font-medium px-2 py-1 rounded-full bg-slate-800 text-cyan-100 border border-slate-600"
        >
          {modeLabel} (alpha = {alpha.toFixed(2)})
        </output>
      </div>

      <label htmlFor="pareto-alpha" className="block text-sm text-slate-200 mb-2">
        Cost priority: {Math.round(alpha * 100)}%
      </label>
      <input
        id="pareto-alpha"
        type="range"
        disabled={!operatorReady}
        min={0}
        max={1}
        step={0.05}
        value={alpha}
        aria-valuetext={`${modeLabel}, cost priority ${Math.round(alpha * 100)} percent`}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-cyan-300 cursor-pointer"
      />

      <div className="flex justify-between gap-3 text-xs text-slate-300 mt-2">
        <span>0.0 · Carbon-Zero</span>
        <span>0.5 · Balanced</span>
        <span>1.0 · Cost-First</span>
      </div>
    </section>
  );
}
