import { AgentDecision, AnomalyItem, EsgLedgerEntry, TwinSnapshot } from "../types/grid";

async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export const api = {
  getState: () => req<TwinSnapshot>("/api/twin/state"),
  controlClock: (action: "play" | "pause" | "step" | "reset") =>
    req<TwinSnapshot>("/api/twin/clock", {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  injectChaos: (event: string) =>
    req<TwinSnapshot>("/api/twin/chaos", {
      method: "POST",
      body: JSON.stringify({ event }),
    }),
  updatePareto: (alpha: number) =>
    req<TwinSnapshot>("/api/optimizer/pareto", {
      method: "POST",
      body: JSON.stringify({ alpha }),
    }),
  submitPolicy: (message: string) =>
    req<AgentDecision>("/api/agent/policy", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  getDecisions: () => req<AgentDecision[]>("/api/agent/decisions"),
  approveDecision: (id: string) =>
    req<AgentDecision>(`/api/agent/decisions/${id}/approve`, { method: "POST" }),
  rejectDecision: (id: string) =>
    req<AgentDecision>(`/api/agent/decisions/${id}/reject`, { method: "POST" }),
  getAnomalies: () => req<AnomalyItem[]>("/api/agent/anomalies"),
  getEsgLedger: () => req<EsgLedgerEntry[]>("/api/esg/ledger"),
};
