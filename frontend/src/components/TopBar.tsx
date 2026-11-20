import { Activity, AlertTriangle, Pause, Play, RotateCcw, StepForward, Zap } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

interface Props {
  snapshot: TwinSnapshot;
  wsConnected: boolean;
  operatorReady: boolean;
  operatorKey: string;
  operatorMessage: string;
  onOperatorKeyChange: (value: string) => void;
  onUnlockOperator: () => void;
  onLockOperator: () => void;
  onClock: (action: "play" | "pause" | "step" | "reset") => void;
  onChaos: (event: string) => void;
}

const CHAOS_OPTIONS = [
  { id: "heatwave", label: "Heatwave Surge (+7°C)" },
  { id: "cloudburst", label: "Sudden Cloudburst (-65% PV)" },
  { id: "carbon_spike", label: "Grid Carbon Spike (+250g)" },
  { id: "hvac_fault", label: "HVAC Zone A Stuck-On (+14kW)" },
  { id: "urgent_ev", label: "Urgent EV Arrival (45kWh/4h)" },
];

export function TopBar({
  snapshot,
  wsConnected,
  operatorReady,
  operatorKey,
  operatorMessage,
  onOperatorKeyChange,
  onUnlockOperator,
  onLockOperator,
  onClock,
  onChaos,
}: Props) {
  return (
    <header className="border-b border-slate-800/80 bg-[#0D1320]/90 backdrop-blur-md px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <div aria-hidden="true" className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Zap className="h-5 w-5 text-slate-950" />
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-white">GridPulse AI</h1>
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-cyan-500/15 text-cyan-100 border border-cyan-500/30">
              Neuro-Symbolic Co-Pilot
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300 mt-1" aria-label="Live data source status">
            <span className="flex items-center gap-1.5" role="status" aria-live="polite">
              <span aria-hidden="true" className={`h-2 w-2 rounded-full ${wsConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
              {wsConnected ? "Live telemetry connected" : "Using REST sync"}
            </span>
            <span aria-hidden="true">•</span>
            <span>Weather: {snapshot.feed_status.weather_source}</span>
            <span aria-hidden="true">•</span>
            <span>Carbon: {snapshot.feed_status.carbon_source}</span>
            <span aria-hidden="true">•</span>
            <span className="text-emerald-300 font-medium">AI mode: {snapshot.feed_status.ai_mode}</span>
          </div>
        </div>
      </div>

      <form
        aria-label="Operator authentication"
        onSubmit={(event) => {
          event.preventDefault();
          onUnlockOperator();
        }}
        className="flex flex-wrap items-center gap-2"
      >
        {operatorReady ? (
          <>
            <span className="text-sm text-emerald-200" role="status">Operator controls unlocked</span>
            <button type="button" onClick={onLockOperator} className="min-h-10 px-3 py-2 rounded-lg border border-slate-600 text-sm text-slate-100 hover:bg-slate-800">
              Lock controls
            </button>
          </>
        ) : (
          <>
            <label htmlFor="operator-access-key" className="sr-only">Operator access key</label>
            <input
              id="operator-access-key"
              type="password"
              value={operatorKey}
              onChange={(event) => onOperatorKeyChange(event.target.value)}
              autoComplete="off"
              spellCheck={false}
              placeholder="Operator access key"
              className="min-h-10 w-44 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-300"
            />
            <button type="submit" className="min-h-10 px-3 py-2 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-slate-950 text-sm font-semibold">
              Unlock controls
            </button>
          </>
        )}
        <span className="sr-only" role="status" aria-live="polite">{operatorMessage}</span>
      </form>

      <section aria-label="Simulation clock controls" className="flex items-center gap-2 bg-slate-900/90 border border-slate-700 rounded-lg px-3 py-2">
        <Activity aria-hidden="true" focusable="false" className="h-4 w-4 text-cyan-300" />
        <span className="text-sm text-slate-200">Simulation clock:</span>
        <time className="text-sm font-bold tabular-nums text-white min-w-12" aria-label={`Simulation hour ${snapshot.sim_hour}`}>
          {String(snapshot.sim_hour).padStart(2, "0")}:00
        </time>
        <button
          type="button"
          disabled={!operatorReady}
          onClick={() => onClock(snapshot.is_running ? "pause" : "play")}
          className="icon-control bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-100 transition"
          aria-label={snapshot.is_running ? "Pause simulation" : "Start simulation"}
          title={snapshot.is_running ? "Pause simulation" : "Start simulation"}
        >
          {snapshot.is_running ? <Pause aria-hidden="true" focusable="false" className="h-4 w-4" /> : <Play aria-hidden="true" focusable="false" className="h-4 w-4" />}
        </button>
        <button type="button" disabled={!operatorReady} onClick={() => onClock("step")} className="icon-control bg-slate-800 hover:bg-slate-700 text-slate-100 transition" aria-label="Advance simulation by one hour" title="Advance simulation by one hour">
          <StepForward aria-hidden="true" focusable="false" className="h-4 w-4" />
        </button>
        <button type="button" disabled={!operatorReady} onClick={() => onClock("reset")} className="icon-control bg-slate-800 hover:bg-slate-700 text-slate-100 transition" aria-label="Reset simulation" title="Reset simulation">
          <RotateCcw aria-hidden="true" focusable="false" className="h-4 w-4" />
        </button>
      </section>

      <section aria-label="Grid fault event controls" className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5 text-sm text-rose-200 font-medium">
          <AlertTriangle aria-hidden="true" focusable="false" className="h-4 w-4" />
          <span>Fault events:</span>
        </div>
        <label htmlFor="chaos-event-select" className="sr-only">Select a grid or equipment fault event</label>
        <select
          id="chaos-event-select"
          disabled={!operatorReady}
          value=""
          onChange={(event) => event.target.value && onChaos(event.target.value)}
          className="bg-slate-900 border border-rose-400/60 text-slate-100 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-rose-300"
        >
          <option value="">Choose an event…</option>
          {CHAOS_OPTIONS.map((event) => <option key={event.id} value={event.id}>{event.label}</option>)}
        </select>
        {snapshot.active_chaos.length > 0 && (
          <button type="button" disabled={!operatorReady} onClick={() => onChaos("reset")} className="min-h-10 text-sm px-3 py-2 rounded-lg bg-rose-500/20 text-rose-100 border border-rose-400/60 hover:bg-rose-500/30 transition">
            Clear active events ({snapshot.active_chaos.length})
          </button>
        )}
      </section>
    </header>
  );
}
