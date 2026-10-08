import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";

import { useSessionEvents } from "./useSessionEvents";
import type { SessionEvent } from "../types";

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  listeners = new Map<string, Set<(event: Event) => void>>();
  closed = false;

  constructor(public url: string) { FakeEventSource.instances.push(this); }
  addEventListener(type: string, listener: (event: Event) => void) {
    const values = this.listeners.get(type) ?? new Set(); values.add(listener); this.listeners.set(type, values);
  }
  removeEventListener(type: string, listener: (event: Event) => void) { this.listeners.get(type)?.delete(listener); }
  close() { this.closed = true; }
  emit(type: string, payload: SessionEvent) {
    const event = new MessageEvent(type, { data: JSON.stringify(payload) });
    this.listeners.get(type)?.forEach((listener) => listener(event));
  }
}

function Harness({ enabled = true }: { enabled?: boolean }) {
  const [count, setCount] = useState(0);
  const { connectionState } = useSessionEvents("session-1", enabled, () => setCount((value) => value + 1));
  return <div><span>{connectionState}</span><output>{count}</output></div>;
}

afterEach(() => { vi.unstubAllGlobals(); FakeEventSource.instances = []; });

describe("useSessionEvents", () => {
  it("connects, filters duplicate event ids and closes cleanly", () => {
    vi.stubGlobal("EventSource", FakeEventSource);
    const view = render(<Harness />);
    const source = FakeEventSource.instances[0];
    expect(source.url).toContain("session-1/events?after=0");

    act(() => source.onopen?.());
    expect(screen.getByText("connected")).toBeInTheDocument();

    const event: SessionEvent = { eventId: 1, topicId: "topic-1", sessionId: "session-1", timestamp: "2026-10-08T04:00:00Z", eventType: "session.state", payload: { status: "running" } };
    act(() => { source.emit("session.state", event); source.emit("session.state", event); });
    expect(screen.getByText("1")).toBeInTheDocument();

    view.rerender(<Harness enabled={false} />);
    expect(source.closed).toBe(true);
  });
});
