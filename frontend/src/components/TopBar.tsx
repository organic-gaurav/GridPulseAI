import { Activity, AlertTriangle, Pause, Play, RotateCcw, StepForward, Zap } from "lucide-react";
import { TwinSnapshot } from "../types/grid";

interface Props {
  snapshot: TwinSnapshot;
  wsConnected: boolean;
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

export function TopBar({ snapshot, wsConnected, onClock, onChaos }: Props) {
  return (
    <header className="border-b border-slate-800/80 bg-[#0D1320]/90 backdrop-blur-md px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Zap className="h-5 w-5 text-slate-950" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-white">GridPulse AI</h1>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
              Neuro-Symbolic Co-Pilot
            </span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
            <span className="flex items-center gap-1">
              <span className={`h-1.5 w-1.5 rounded-full ${wsConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
              {wsConnected ? "WS Live" : "REST Sync"}
            </span>
            <span>•</span>
            <span>{snapshot.feed_status.weather_source}</span>
            <span>•</span>
            <span>{snapshot.feed_status.carbon_source}</span>
            <span>•</span>
            <span className="text-emerald-400 font-medium">{snapshot.feed_status.ai_mode}</span>
          </div>
        </div>
      </div>

      {/* Simulation Clock */}
      <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-1.5">
        <Activity className="h-4 w-4 text-cyan-400" />
        <span className="text-xs text-slate-400">Sim Clock:</span>
        <span className="text-sm font-bold tabular-nums text-white w-12">
          {String(snapshot.sim_hour).padStart(2, "0")}:00
        </span>
        <button
          onClick={() => onClock(snapshot.is_running ? "pause" : "play")}
          className="p-1.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 transition"
          title={snapshot.is_running ? "Pause" : "Play"}
        >
          {snapshot.is_running ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
        </button>
        <button
          onClick={() => onClock("step")}
          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
          title="Step +1h"
        >
          <StepForward className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => onClock("reset")}
          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          title="Reset Simulation"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Chaos Event Injector */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-rose-400 font-medium">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>Chaos:</span>
        </div>
        <select
          value=""
          onChange={(e) => e.target.value && onChaos(e.target.value)}
          className="bg-slate-900 border border-rose-500/30 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-rose-400"
        >
          <option value="" disabled>
            Inject Grid / Fault Event...
          </option>
          {CHAOS_OPTIONS.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
        {snapshot.active_chaos.length > 0 && (
          <button
            onClick={() => onChaos("reset")}
            className="text-xs px-2.5 py-1.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30 transition"
          >
            Clear ({snapshot.active_chaos.length})
          </button>
        )}
      </div>
    </header>
  );
}
