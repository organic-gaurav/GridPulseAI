import type { AgentDecision, AnomalyItem, EsgLedgerEntry, TwinSnapshot } from "../types/grid";

// Empty VITE_API_URL uses the Vite proxy during local development.
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
const endpoint = (path: string) => `${API_BASE_URL}${path}`;

// Kept in memory only. It is never written to localStorage or embedded in the build.
let operatorAccessToken = "";

export function clearOperatorAccessToken(): void {
  operatorAccessToken = "";
}

async function req<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (operatorAccessToken) {
    headers.set("Authorization", `Bearer ${operatorAccessToken}`);
  }

  const response = await fetch(endpoint(url), {
    ...options,
    headers,
    mode: "cors",
    credentials: "omit",
  });

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 400);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function verifyOperatorAccess(token: string): Promise<void> {
  operatorAccessToken = token.trim();
  try {
    await req<{ authenticated: boolean }>("/api/auth/check");
  } catch (error) {
    operatorAccessToken = "";
    throw error;
  }
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
    req<AgentDecision>(`/api/agent/decisions/${encodeURIComponent(id)}/approve`, { method: "POST" }),
  rejectDecision: (id: string) =>
    req<AgentDecision>(`/api/agent/decisions/${encodeURIComponent(id)}/reject`, { method: "POST" }),
  getAnomalies: () => req<AnomalyItem[]>("/api/agent/anomalies"),
  getEsgLedger: () => req<EsgLedgerEntry[]>("/api/esg/ledger"),
};

export { clearOperatorAccessToken as clearAccessToken };
