import { useEffect, useRef, useState } from "react";
import type { SessionEvent, SessionEventType } from "../types";

export type ConnectionState = "idle" | "connecting" | "connected" | "reconnecting" | "error";

const EVENT_TYPES: SessionEventType[] = [
  "session.state",
  "expert.status",
  "transcript.append",
  "branch.created",
  "summary.ready",
  "stream.error",
  "heartbeat",
];

export function useSessionEvents(
  sessionId: string | null,
  enabled: boolean,
  onEvent: (event: SessionEvent) => void,
) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const callbackRef = useRef(onEvent);
  const lastEventId = useRef(0);
  callbackRef.current = onEvent;

  useEffect(() => {
    if (!sessionId || !enabled) {
      setConnectionState("idle");
      return;
    }
    setConnectionState("connecting");
    const source = new EventSource(`/api/v1/sessions/${sessionId}/events?after=${lastEventId.current}`);

    source.onopen = () => setConnectionState("connected");
    source.onerror = () => setConnectionState((current) => current === "connected" ? "reconnecting" : "error");
    const handle = (raw: Event) => {
      const message = raw as MessageEvent<string>;
      try {
        const event = JSON.parse(message.data) as SessionEvent;
        if (event.sessionId !== sessionId || event.eventId <= lastEventId.current) return;
        lastEventId.current = event.eventId;
        if (event.eventType !== "heartbeat") callbackRef.current(event);
      } catch {
        setConnectionState("error");
      }
    };
    for (const type of EVENT_TYPES) source.addEventListener(type, handle);
    return () => {
      for (const type of EVENT_TYPES) source.removeEventListener(type, handle);
      source.close();
    };
  }, [enabled, sessionId]);

  return { connectionState, lastEventId: lastEventId.current };
}
