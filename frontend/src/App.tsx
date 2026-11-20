import { useEffect, useState } from "react";
import { BarChart3, Cpu, FileSpreadsheet } from "lucide-react";
import { AgentPanel } from "./components/AgentPanel";
import { AssetsView } from "./components/AssetsView";
import { DispatchChart } from "./components/DispatchChart";
import { EsgLedgerView } from "./components/EsgLedgerView";
import { KpiStrip } from "./components/KpiStrip";
import { ParetoControl } from "./components/ParetoControl";
import { PowerFlowDiagram } from "./components/PowerFlowDiagram";
import { ReasoningModal } from "./components/ReasoningModal";
import { TopBar } from "./components/TopBar";
import { useGridSocket } from "./hooks/useGridSocket";
import { api, clearAccessToken, verifyOperatorAccess } from "./lib/api";
import { AgentDecision, AnomalyItem, EsgLedgerEntry } from "./types/grid";

type View = "overview" | "assets" | "esg";

const VIEWS: { id: View; label: string; icon: typeof BarChart3 }[] = [
  { id: "overview", label: "Command Center", icon: BarChart3 },
  { id: "assets", label: "Thermal & EV Assets", icon: Cpu },
  { id: "esg", label: "ESG Audit Ledger", icon: FileSpreadsheet },
];

export function App() {
  const { snapshot, setSnapshot, connected } = useGridSocket();
  const [view, setView] = useState<View>("overview");
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [ledger, setLedger] = useState<EsgLedgerEntry[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<AgentDecision | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [operatorKey, setOperatorKey] = useState("");
  const [operatorReady, setOperatorReady] = useState(false);
  const [operatorMessage, setOperatorMessage] = useState("");

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  }

  async function unlockOperator() {
    try {
      await verifyOperatorAccess(operatorKey);
      setOperatorReady(true);
      setOperatorKey("");
      setOperatorMessage("Operator controls are unlocked for this tab session.");
    } catch {
      setOperatorReady(false);
      setOperatorMessage("Access key was rejected or operator authentication is not configured on the server.");
    }
  }

  function lockOperator() {
    clearAccessToken();
    setOperatorReady(false);
    setOperatorKey("");
    setOperatorMessage("Operator controls locked.");
  }

  async function refreshAgentData() {
    const [decs, anoms, esg] = await Promise.all([
      api.getDecisions(),
      api.getAnomalies(),
      api.getEsgLedger(),
    ]);
    setDecisions(decs);
    setAnomalies(anoms);
    setLedger(esg);
  }

  useEffect(() => {
    refreshAgentData().catch(() => {});
  }, [snapshot?.sim_hour, snapshot?.active_chaos.length]);

  if (!snapshot) {
    return (
      <main className="min-h-screen bg-[#090D16] flex items-center justify-center text-slate-300 text-sm px-6">
        <p role="status" aria-live="polite" aria-busy="true">
          Connecting to GridPulse AI Microgrid Digital Twin…
        </p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col">
      <a
        href="#main-content"
        className="skip-link"
      >
        Skip to main content
      </a>

      <TopBar
        snapshot={snapshot}
        wsConnected={connected}
        operatorReady={operatorReady}
        operatorKey={operatorKey}
        operatorMessage={operatorMessage}
        onOperatorKeyChange={setOperatorKey}
        onUnlockOperator={unlockOperator}
        onLockOperator={lockOperator}
        onClock={async (action) => {
          const next = await api.controlClock(action);
          setSnapshot(next);
          if (action === "step" || action === "reset") refreshAgentData();
        }}
        onChaos={async (event) => {
          const next = await api.injectChaos(event);
          setSnapshot(next);
          refreshAgentData();
          showToast(event === "reset" ? "Chaos events cleared" : `Injected chaos: ${event}`);
        }}
      />

      <nav
        aria-label="Dashboard sections"
        className="border-b border-slate-800/80 bg-[#0D1320]/50 px-4 flex flex-wrap gap-1"
      >
        {VIEWS.map((item) => {
          const Icon = item.icon;
          const active = view === item.id;
          return (
            <button
              key={item.id}
              type="button"
              aria-pressed={active}
              onClick={() => setView(item.id)}
              className={`dashboard-nav-button px-4 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition ${ 
                active ? "border-cyan-400 text-cyan-200" : "border-transparent text-slate-300 hover:text-white"
              }`}
            >
              <Icon aria-hidden="true" focusable="false" className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <main id="main-content" tabIndex={-1} className="flex-1 p-4 max-w-[1600px] w-full mx-auto space-y-4">
        <KpiStrip snapshot={snapshot} />

        {view === "overview" && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
            <div className="xl:col-span-8 space-y-4">
              <PowerFlowDiagram snapshot={snapshot} />
              <DispatchChart snapshot={snapshot} />
              <ParetoControl
                alpha={snapshot.pareto_alpha}
                operatorReady={operatorReady}
                onChange={async (alpha) => {
                  const next = await api.updatePareto(alpha);
                  setSnapshot(next);
                }}
              />
            </div>
            <div className="xl:col-span-4">
              <AgentPanel
                decisions={decisions}
                anomalies={anomalies}
                operatorReady={operatorReady}
                onSubmitPolicy={async (msg) => {
                  const dec = await api.submitPolicy(msg);
                  await refreshAgentData();
                  const next = await api.getState();
                  setSnapshot(next);
                  showToast(
                    dec.tier === 1
                      ? `Autonomous Tier-1 executed: ${dec.title}`
                      : `Tier-2 HITL Approval queued: ${dec.title}`
                  );
                }}
                onApprove={async (id) => {
                  await api.approveDecision(id);
                  await refreshAgentData();
                  setSnapshot(await api.getState());
                  showToast("Tier-2 proposal approved and applied to optimizer");
                }}
                onReject={async (id) => {
                  await api.rejectDecision(id);
                  await refreshAgentData();
                  showToast("Tier-2 proposal rejected");
                }}
                onInspect={(d) => setSelectedTrace(d)}
              />
            </div>
          </div>
        )}

        {view === "assets" && <AssetsView snapshot={snapshot} />}
        {view === "esg" && <EsgLedgerView entries={ledger} />}
      </main>

      <ReasoningModal decision={selectedTrace} onClose={() => setSelectedTrace(null)} />

      {toast && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="fixed bottom-4 right-4 z-50 bg-slate-900 border border-cyan-500/40 text-cyan-100 px-4 py-3 rounded-lg shadow-xl text-sm"
        >
          {toast}
        </div>
      )}
    </div>
  );
}

export default App;
