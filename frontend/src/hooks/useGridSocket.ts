import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { TwinSnapshot } from "../types/grid";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");

function getWebSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const defaultBase = `${protocol}//${window.location.host}`;
  const base = API_BASE_URL
    ? API_BASE_URL.replace(/^http:/, "ws:").replace(/^https:/, "wss:")
    : defaultBase;
  return `${base}/ws/telemetry`;
}

export function useGridSocket() {
  const [snapshot, setSnapshot] = useState<TwinSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let active = true;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    api.getState().then((data) => {
      if (active) setSnapshot(data);
    }).catch(() => {});

    function connect() {
      if (!active) return;

      const ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        if (active) setConnected(true);
      };
      ws.onmessage = (ev) => {
        try {
          const parsed = JSON.parse(ev.data) as TwinSnapshot;
          if (active) setSnapshot(parsed);
        } catch {
          // Ignore malformed telemetry messages.
        }
      };
      ws.onerror = () => {
        ws.close();
      };
      ws.onclose = () => {
        if (active) {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 2500);
        }
      };
    }

    connect();
    return () => {
      active = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return { snapshot, setSnapshot, connected };
}
