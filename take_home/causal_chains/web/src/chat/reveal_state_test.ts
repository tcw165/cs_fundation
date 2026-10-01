import { describe, expect, it } from "vitest";

import type { ChatItem } from "./chat_item";
import { initial_reveal_state, reveal_reducer } from "./reveal_state";

function markdown(message_id: string, text: string): ChatItem {
  return {
    kind: "markdown",
    message_id,
    role: "agent",
    text,
    created_timestamp: "2026-09-30T00:00:00+00:00",
  };
}

function heartbeat(message_id: string): ChatItem {
  return { kind: "heartbeat", message_id, role: "meta" };
}

describe("reveal_reducer", () => {
  it("holds the next message until the current animation finishes", () => {
    let state = reveal_reducer(initial_reveal_state, {
      type: "enqueue",
      item: markdown("a", "one"),
    });
    state = reveal_reducer(state, { type: "enqueue", item: markdown("b", "two") });
    state = reveal_reducer(state, { type: "start" });
    expect(state.shown.map((item) => item.message_id)).toEqual(["a"]);
    expect(state.phase).toBe("animating");
    const blocked = reveal_reducer(state, { type: "start" });
    expect(blocked.shown.map((item) => item.message_id)).toEqual(["a"]);
    expect(blocked.pending).toHaveLength(1);
    state = reveal_reducer(state, { type: "finish" });
    state = reveal_reducer(state, { type: "start" });
    expect(state.shown.map((item) => item.message_id)).toEqual(["a", "b"]);
    expect(state.animating_id).toBe("b");
  });

  it("collapses consecutive heartbeats into one queued beat", () => {
    let state = reveal_reducer(initial_reveal_state, {
      type: "enqueue",
      item: heartbeat("h1"),
    });
    state = reveal_reducer(state, { type: "enqueue", item: heartbeat("h2") });
    expect(state.pending.map((item) => item.message_id)).toEqual(["h2"]);
  });

  it("shows stored history without queueing an animation", () => {
    const user: ChatItem = {
      kind: "markdown",
      message_id: "u",
      role: "user",
      text: "earlier",
      created_timestamp: "2026-09-30T00:00:00+00:00",
    };
    let state = reveal_reducer(initial_reveal_state, { type: "restore", item: user });
    state = reveal_reducer(state, { type: "restore", item: markdown("a", "saved") });
    state = reveal_reducer(state, { type: "restore", item: heartbeat("h") });
    state = reveal_reducer(state, { type: "restore", item: markdown("a", "saved") });
    expect(state.pending).toEqual([]);
    expect(state.phase).toBe("idle");
    expect(state.log).toEqual([
      { kind: "user", id: "u", text: "earlier" },
      { kind: "agent", item: markdown("a", "saved") },
    ]);
  });
});
