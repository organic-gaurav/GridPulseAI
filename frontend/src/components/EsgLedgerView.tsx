import { Download } from "lucide-react";
import { EsgLedgerEntry } from "../types/grid";

export function EsgLedgerView({ entries }: { entries: EsgLedgerEntry[] }) {
  function downloadJson() {
    const blob = new Blob([JSON.stringify(entries, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gridpulse_esg_ledger.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <section aria-labelledby="esg-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="esg-heading" className="text-base font-semibold text-white">
            Scope 2 ESG &amp; Counterfactual Audit Ledger
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            Hourly verified delta: Agent-Optimized Twin vs. Unoptimized Baseline Twin
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a
            href="/api/esg/export/csv"
            download="gridpulse_esg_ledger.csv"
            className="min-h-10 px-3 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-100 border border-emerald-400/60 text-sm font-medium flex items-center gap-1.5"
          >
            <Download aria-hidden="true" focusable="false" className="h-4 w-4" /> Export CSV
          </a>
          <button
            type="button"
            onClick={downloadJson}
            className="min-h-10 px-3 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-100 border border-cyan-400/60 text-sm font-medium flex items-center gap-1.5"
          >
            <Download aria-hidden="true" focusable="false" className="h-4 w-4" /> Export JSON
          </button>
        </div>
      </div>

      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="ESG audit ledger table; scroll horizontally to see all columns">
        <table className="w-full text-left text-sm tabular-nums">
          <caption className="sr-only">Hourly energy, cost, and carbon comparisons between optimized and baseline operation.</caption>
          <thead className="border-b border-slate-700 text-slate-200">
            <tr>
              <th scope="col" className="py-3 px-2">Hour</th>
              <th scope="col" className="py-3 px-2">Opt Grid (kWh)</th>
              <th scope="col" className="py-3 px-2">Base Grid (kWh)</th>
              <th scope="col" className="py-3 px-2">Solar PV (kWh)</th>
              <th scope="col" className="py-3 px-2">Cost Saved ($)</th>
              <th scope="col" className="py-3 px-2">CO₂ Avoided (kg)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-300">
                  Step or play the simulation clock to record verified hourly ESG ledger entries.
                </td>
              </tr>
            ) : (
              entries.map((e) => (
                <tr key={e.hour} className="hover:bg-slate-900/50">
                  <th scope="row" className="py-3 px-2 font-medium text-white">{String(e.hour).padStart(2, "0")}:00</th>
                  <td className="py-3 px-2 text-cyan-200">{e.opt_grid_kwh.toFixed(1)}</td>
                  <td className="py-3 px-2 text-rose-200">{e.base_grid_kwh.toFixed(1)}</td>
                  <td className="py-3 px-2 text-amber-200">{e.pv_kwh.toFixed(1)}</td>
                  <td className="py-3 px-2 text-emerald-200 font-semibold">+${e.cost_saved_usd.toFixed(2)}</td>
                  <td className="py-3 px-2 text-emerald-200 font-semibold">+{e.carbon_avoided_kg.toFixed(2)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
