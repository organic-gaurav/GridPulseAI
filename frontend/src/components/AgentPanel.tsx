import { useState } from "react";
import { AlertCircle, Bot, Check, Eye, Send, ShieldAlert, X } from "lucide-react";
import { AgentDecision, AnomalyItem } from "../types/grid";

interface Props {
  decisions: AgentDecision[];
  anomalies: AnomalyItem[];
  onSubmitPolicy: (msg: string) => Promise<void>;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  onInspect: (d: AgentDecision) => void;
}

const PRESETS = [
  "Prioritize Carbon-Zero mode for the next 24h",
  "Keep 30% battery reserve for backup",
  "Widen Zone A comfort band to 26°C to save peak",
  "Prioritize EV-1 Fleet Van ready by 3 PM",
];

export function AgentPanel({
  decisions,
  anomalies,
  onSubmitPolicy,
  onApprove,
  onReject,
  onInspect,
}: Props) {
  const [tab, setTab] = useState<"hitl" | "chat" | "anomalies">("hitl");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const pending = decisions.filter((d) => d.status === "pending");

  async function handleSend(msg: string) {
    if (!msg.trim() || busy) return;
    setBusy(true);
    try {
      await onSubmitPolicy(msg.trim());
      setInput("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-[#111827]/90 border border-slate-800 rounded-xl flex flex-col h-full min-h-[520px]">
      {/* Tabs */}
      <div className="flex border-b border-slate-800 text-xs font-medium">
        <button
          onClick={() => setTab("hitl")}
          className={`flex-1 py-3 px-2 flex items-center justify-center gap-1.5 border-b-2 transition ${
            tab === "hitl" ? "border-cyan-400 text-cyan-300" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldAlert className="h-3.5 w-3.5" />
          Approvals ({pending.length})
        </button>
        <button
          onClick={() => setTab("chat")}
          className={`flex-1 py-3 px-2 flex items-center justify-center gap-1.5 border-b-2 transition ${
            tab === "chat" ? "border-cyan-400 text-cyan-300" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Bot className="h-3.5 w-3.5" />
          Policy Chat
        </button>
        <button
          onClick={() => setTab("anomalies")}
          className={`flex-1 py-3 px-2 flex items-center justify-center gap-1.5 border-b-2 transition ${
            tab === "anomalies"
              ? "border-rose-400 text-rose-300"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <AlertCircle className="h-3.5 w-3.5" />
          Anomalies ({anomalies.length})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 p-3 overflow-y-auto space-y-2.5">
        {tab === "hitl" && (
          <>
            {decisions.length === 0 ? (
              <div className="text-xs text-slate-400 text-center py-8">
                No agent decisions yet. Try submitting a policy in Policy Chat!
              </div>
            ) : (
              decisions.map((d) => (
                <div key={d.id} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs font-semibold text-white">{d.title}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{d.rationale}</div>
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${
                        d.status === "pending"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : d.status === "executed" || d.status === "approved"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      }`}
                    >
                      {d.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">Tier {d.tier}</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-300">
                      CO₂: {d.carbon_impact_kg >= 0 ? `-${d.carbon_impact_kg}` : `+${Math.abs(d.carbon_impact_kg)}`} kg
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300">{d.comfort_impact}</span>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={() => onInspect(d)}
                      className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                    >
                      <Eye className="h-3 w-3" /> Trace
                    </button>
                    {d.status === "pending" && (
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => onApprove(d.id)}
                          className="px-2 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-[11px] flex items-center gap-1"
                        >
                          <Check className="h-3 w-3" /> Approve
                        </button>
                        <button
                          onClick={() => onReject(d.id)}
                          className="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-[11px] flex items-center gap-1"
                        >
                          <X className="h-3 w-3" /> Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </>
        )}

        {tab === "chat" && (
          <div className="flex flex-col h-full justify-between space-y-3">
            <div className="space-y-2">
              <p className="text-[11px] text-slate-400">
                Type an operational policy in plain English or click a preset:
              </p>
              <div className="grid grid-cols-1 gap-1.5">
                {PRESETS.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleSend(p)}
                    disabled={busy}
                    className="text-left text-[11px] px-2.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition"
                  >
                    “{p}”
                  </button>
                ))}
              </div>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend(input);
              }}
              className="flex gap-2 pt-2 border-t border-slate-800"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="e.g. Keep 35% battery reserve..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={busy}
                className="px-3 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs flex items-center gap-1 disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </form>
          </div>
        )}

        {tab === "anomalies" && (
          <>
            {anomalies.length === 0 ? (
              <div className="text-xs text-emerald-400 text-center py-8">
                All subsystems nominal. Zero physics-residual anomalies detected.
              </div>
            ) : (
              anomalies.map((a) => (
                <div key={a.id} className="bg-rose-950/30 border border-rose-500/30 rounded-lg p-3 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-300">{a.anomaly_type}</span>
                    <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                      {a.severity}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300">{a.description}</p>
                  <p className="text-[10px] text-rose-400 tabular-nums">
                    Estimated Waste: {a.estimated_waste_kw.toFixed(1)} kW • Hour {a.sim_hour}:00
                  </p>
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}
