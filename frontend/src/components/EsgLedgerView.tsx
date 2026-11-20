import { Download } from "lucide-react";
import { EsgLedgerEntry } from "../types/grid";

export function EsgLedgerView({ entries }: { entries: EsgLedgerEntry[] }) {
  function downloadJson() {
    const blob = new Blob([JSON.stringify(entries, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gridpulse_esg_ledger.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">Scope 2 ESG & Counterfactual Audit Ledger</h2>
          <p className="text-xs text-slate-400">
            Hourly verified delta: Agent-Optimized Twin vs. Unoptimized Baseline Twin
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href="/api/esg/export/csv"
            download="gridpulse_esg_ledger.csv"
            className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-medium flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" /> Export CSV
          </a>
          <button
            onClick={downloadJson}
            className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 text-xs font-medium flex items-center gap-1.5"
          >
            <Download className="h-3.5 w-3.5" /> Export JSON
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs tabular-nums">
          <thead className="border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 px-2">Hour</th>
              <th className="py-2 px-2">Opt Grid (kWh)</th>
              <th className="py-2 px-2">Base Grid (kWh)</th>
              <th className="py-2 px-2">Solar PV (kWh)</th>
              <th className="py-2 px-2">Cost Saved ($)</th>
              <th className="py-2 px-2">CO₂ Avoided (kg)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400">
                  Step or play the simulation clock to record verified hourly ESG ledger entries.
                </td>
              </tr>
            ) : (
              entries.map((e, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50">
                  <td className="py-2 px-2 font-medium text-white">{String(e.hour).padStart(2, "0")}:00</td>
                  <td className="py-2 px-2 text-cyan-300">{e.opt_grid_kwh.toFixed(1)}</td>
                  <td className="py-2 px-2 text-rose-300">{e.base_grid_kwh.toFixed(1)}</td>
                  <td className="py-2 px-2 text-amber-300">{e.pv_kwh.toFixed(1)}</td>
                  <td className="py-2 px-2 text-emerald-400 font-semibold">+${e.cost_saved_usd.toFixed(2)}</td>
                  <td className="py-2 px-2 text-emerald-400 font-semibold">+{e.carbon_avoided_kg.toFixed(2)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
