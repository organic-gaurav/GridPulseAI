import { X } from "lucide-react";
import { AgentDecision } from "../types/grid";

interface Props {
  decision: AgentDecision | null;
  onClose: () => void;
}

export function ReasoningModal({ decision, onClose }: Props) {
  if (!decision) return null;

  const steps = [
    { label: "1. Trigger Event", value: decision.trace.trigger_event },
    { label: "2. Physics Check", value: decision.trace.physics_check },
    { label: "3. Solver Delta", value: decision.trace.solver_delta },
    { label: "4. Guardrail Tier", value: decision.trace.guardrail_tier },
    { label: "5. Rationale", value: decision.trace.rationale },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-slate-700 rounded-xl max-w-lg w-full p-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">{decision.title}</h3>
            <p className="text-xs text-slate-400">Neuro-Symbolic Reasoning Trace • {decision.created_at}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-slate-800 text-slate-400">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3">
          {steps.map((s) => (
            <div key={s.label} className="bg-slate-900/80 border border-slate-800 rounded-lg p-3">
              <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">{s.label}</div>
              <div className="text-xs text-slate-200 mt-1">{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
