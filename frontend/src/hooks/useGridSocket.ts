import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { TwinSnapshot } from "../types/grid";

export function useGridSocket() {
  const [snapshot, setSnapshot] = useState<TwinSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let active = true;
    api.getState().then((data) => {
      if (active) setSnapshot(data);
    }).catch(() => {});

    function connect() {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${proto}//${window.location.host}/ws/telemetry`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (active) setConnected(true);
      };
      ws.onmessage = (ev) => {
        try {
          const parsed = JSON.parse(ev.data) as TwinSnapshot;
          if (active) setSnapshot(parsed);
        } catch {
          // ignore malformed
        }
      };
      ws.onclose = () => {
        if (active) {
          setConnected(false);
          setTimeout(connect, 2500);
        }
      };
    }

    connect();
    return () => {
      active = false;
      wsRef.current?.close();
    };
  }, []);

  return { snapshot, setSnapshot, connected };
}
