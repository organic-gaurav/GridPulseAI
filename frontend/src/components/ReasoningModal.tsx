import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { AgentDecision } from "../types/grid";

interface Props {
  decision: AgentDecision | null;
  onClose: () => void;
}

export function ReasoningModal({ decision, onClose }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!decision) return;

    previousFocusRef.current = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
      );
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!dialogRef.current.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [decision?.id]);

  if (!decision) return null;

  const steps = [
    { label: "1. Trigger Event", value: decision.trace.trigger_event },
    { label: "2. Physics Check", value: decision.trace.physics_check },
    { label: "3. Solver Delta", value: decision.trace.solver_delta },
    { label: "4. Guardrail Tier", value: decision.trace.guardrail_tier },
    { label: "5. Rationale", value: decision.trace.rationale },
  ];

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="reasoning-modal-title"
        aria-describedby="reasoning-modal-description"
        className="bg-[#111827] border border-slate-600 rounded-xl max-w-lg w-full max-h-[85vh] overflow-y-auto p-5 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-700 pb-3 mb-4">
          <div>
            <h2 id="reasoning-modal-title" className="text-base font-bold text-white">{decision.title}</h2>
            <p id="reasoning-modal-description" className="text-sm text-slate-300 mt-1">
              Neuro-Symbolic Reasoning Trace · {decision.created_at}
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close reasoning trace"
            className="icon-control shrink-0 hover:bg-slate-800 text-slate-100"
          >
            <X aria-hidden="true" focusable="false" className="h-5 w-5" />
          </button>
        </div>

        <ol className="space-y-3">
          {steps.map((step) => (
            <li key={step.label} className="bg-slate-900/80 border border-slate-700 rounded-lg p-3">
              <h3 className="text-sm font-semibold text-cyan-200 uppercase tracking-wide">{step.label}</h3>
              <p className="text-sm text-slate-100 mt-1 whitespace-pre-wrap">{step.value}</p>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
