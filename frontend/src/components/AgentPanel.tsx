import { useState, type KeyboardEvent } from "react";
import { AlertCircle, Bot, Check, Eye, Send, ShieldAlert, X } from "lucide-react";
import { AgentDecision, AnomalyItem } from "../types/grid";

interface Props {
  decisions: AgentDecision[];
  anomalies: AnomalyItem[];
  operatorReady: boolean;
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

type AgentTab = "hitl" | "chat" | "anomalies";
const TABS: { id: AgentTab; label: string; icon: typeof ShieldAlert }[] = [
  { id: "hitl", label: "Approvals", icon: ShieldAlert },
  { id: "chat", label: "Policy Chat", icon: Bot },
  { id: "anomalies", label: "Anomalies", icon: AlertCircle },
];

export function AgentPanel({
  decisions,
  anomalies,
  operatorReady,
  onSubmitPolicy,
  onApprove,
  onReject,
  onInspect,
}: Props) {
  const [tab, setTab] = useState<AgentTab>("hitl");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const pending = decisions.filter((d) => d.status === "pending");

  async function handleSend(msg: string) {
    if (!operatorReady || !msg.trim() || busy) return;
    setBusy(true);
    setMessage("Submitting policy…");
    try {
      await onSubmitPolicy(msg.trim());
      setInput("");
      setMessage("Policy submitted successfully.");
    } catch {
      setMessage("The policy could not be submitted. Check the connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, current: AgentTab) {
    const currentIndex = TABS.findIndex((item) => item.id === current);
    let nextIndex = currentIndex;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = (currentIndex + 1) % TABS.length;
    else if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = (currentIndex - 1 + TABS.length) % TABS.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = TABS.length - 1;
    else return;

    event.preventDefault();
    const nextTab = TABS[nextIndex].id;
    setTab(nextTab);
    document.getElementById(`agent-tab-${nextTab}`)?.focus();
  }

  return (
    <section aria-labelledby="agent-panel-heading" className="bg-[#111827]/90 border border-slate-800 rounded-xl flex flex-col h-full min-h-[520px]">
      <h2 id="agent-panel-heading" className="sr-only">AI agent operations</h2>
      {!operatorReady && <p className="px-3 py-2 text-sm text-amber-100 bg-amber-500/10 border-b border-amber-400/30" role="status">Unlock operator controls to submit policies or approve actions. Read-only dashboard data remains available.</p>}
      <div role="tablist" aria-label="AI agent tools" className="flex border-b border-slate-700 text-sm font-medium">
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = tab === id;
          const count = id === "hitl" ? pending.length : id === "anomalies" ? anomalies.length : null;
          return (
            <button
              key={id}
              id={`agent-tab-${id}`}
              type="button"
              role="tab"
              aria-selected={active}
              aria-controls="agent-tabpanel"
              tabIndex={active ? 0 : -1}
              onClick={() => setTab(id)}
              onKeyDown={(event) => handleTabKeyDown(event, id)}
              className={`flex-1 min-h-12 py-3 px-2 flex items-center justify-center gap-1.5 border-b-2 transition ${active ? "border-cyan-300 text-cyan-100" : "border-transparent text-slate-300 hover:text-white"}`}
            >
              <Icon aria-hidden="true" focusable="false" className="h-4 w-4" />
              <span>{label}{count !== null ? ` (${count})` : ""}</span>
            </button>
          );
        })}
      </div>

      <div
        id="agent-tabpanel"
        role="tabpanel"
        aria-labelledby={`agent-tab-${tab}`}
        tabIndex={0}
        className="flex-1 p-3 overflow-y-auto space-y-3"
      >
        {tab === "hitl" && (
          <>
            {decisions.length === 0 ? (
              <p className="text-sm text-slate-300 text-center py-8">
                No agent decisions yet. Try submitting a policy in Policy Chat.
              </p>
            ) : (
              decisions.map((d) => (
                <article key={d.id} className="bg-slate-900/90 border border-slate-700 rounded-lg p-3 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-semibold text-white">{d.title}</h3>
                      <p className="text-sm text-slate-300 mt-1">{d.rationale}</p>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium shrink-0 ${
                        d.status === "pending"
                          ? "bg-amber-500/20 text-amber-100 border border-amber-400/50"
                          : d.status === "executed" || d.status === "approved"
                          ? "bg-emerald-500/20 text-emerald-100 border border-emerald-400/50"
                          : "bg-rose-500/20 text-rose-100 border border-rose-400/50"
                      }`}
                    >
                      {d.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="px-2 py-1 rounded bg-slate-800 text-slate-100">Tier {d.tier}</span>
                    <span className="px-2 py-1 rounded bg-slate-800 text-emerald-100">
                      CO₂: {d.carbon_impact_kg >= 0 ? `-${d.carbon_impact_kg}` : `+${Math.abs(d.carbon_impact_kg)}`} kg
                    </span>
                    <span className="px-2 py-1 rounded bg-slate-800 text-cyan-100">{d.comfort_impact}</span>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => onInspect(d)}
                      className="min-h-10 px-2 text-sm text-cyan-200 hover:text-white flex items-center gap-2"
                    >
                      <Eye aria-hidden="true" focusable="false" className="h-4 w-4" /> Inspect reasoning trace
                    </button>
                    {d.status === "pending" && (
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => onApprove(d.id)}
                          disabled={!operatorReady}
                          className="min-h-10 px-3 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-100 border border-emerald-400/50 text-sm flex items-center gap-2"
                        >
                          <Check aria-hidden="true" focusable="false" className="h-4 w-4" /> Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => onReject(d.id)}
                          disabled={!operatorReady}
                          className="min-h-10 px-3 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-100 border border-rose-400/50 text-sm flex items-center gap-2"
                        >
                          <X aria-hidden="true" focusable="false" className="h-4 w-4" /> Reject
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              ))
            )}
          </>
        )}

        {tab === "chat" && (
          <div className="flex flex-col h-full justify-between space-y-4">
            <div className="space-y-3">
              <p className="text-sm text-slate-300">
                Type an operational policy in plain English or choose a suggested policy:
              </p>
              <div className="grid grid-cols-1 gap-2">
                {PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => handleSend(preset)}
                    disabled={busy || !operatorReady}
                    className="min-h-11 text-left text-sm px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-100 transition"
                  >
                    “{preset}”
                  </button>
                ))}
              </div>
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                handleSend(input);
              }}
              className="flex flex-wrap gap-2 pt-3 border-t border-slate-700"
            >
              <label htmlFor="agent-policy-input" className="sr-only">Operational policy instruction</label>
              <input
                id="agent-policy-input"
                disabled={!operatorReady}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="e.g. Keep 35% battery reserve…"
                aria-describedby="agent-policy-help"
                className="min-h-11 flex-1 min-w-0 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-300"
              />
              <button
                type="submit"
                disabled={!operatorReady || busy || !input.trim()}
                aria-label="Submit operational policy"
                className="min-h-11 min-w-11 px-3 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Send aria-hidden="true" focusable="false" className="h-4 w-4" />
                <span className="hidden sm:inline">Send</span>
              </button>
              <p id="agent-policy-help" className="w-full text-xs text-slate-300">
                Policies are evaluated by the GridPulse AI agent before they are applied.
              </p>
            </form>
            <p className="text-sm text-cyan-100" role="status" aria-live="polite" aria-atomic="true">
              {busy ? "Submitting policy…" : message}
            </p>
          </div>
        )}

        {tab === "anomalies" && (
          <>
            {anomalies.length === 0 ? (
              <p className="text-sm text-emerald-200 text-center py-8">
                All subsystems nominal. Zero physics-residual anomalies detected.
              </p>
            ) : (
              anomalies.map((anomaly) => (
                <article key={anomaly.id} className="bg-rose-950/40 border border-rose-400/50 rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-bold text-rose-100">{anomaly.anomaly_type}</h3>
                    <span className="text-xs uppercase px-2 py-1 rounded bg-rose-500/20 text-rose-100 border border-rose-400/40">
                      {anomaly.severity}
                    </span>
                  </div>
                  <p className="text-sm text-slate-100">{anomaly.description}</p>
                  <p className="text-sm text-rose-100 tabular-nums">
                    Estimated waste: {anomaly.estimated_waste_kw.toFixed(1)} kW · Hour {anomaly.sim_hour}:00
                  </p>
                </article>
              ))
            )}
          </>
        )}
      </div>
    </section>
  );
}
