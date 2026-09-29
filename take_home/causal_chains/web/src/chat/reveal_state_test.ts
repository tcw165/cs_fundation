import { describe, expect, it } from "vitest";

import type { ChatItem } from "./chat_item";
import { initial_reveal_state, reveal_reducer } from "./reveal_state";

function markdown(message_id: string, text: string): ChatItem {
  return { type: "markdown", message_id, role: "agent", text };
}

function heartbeat(message_id: string): ChatItem {
  return { type: "heartbeat", message_id, role: "meta" };
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

  it("drops heartbeats so they never appear in the transcript", () => {
    let state = reveal_reducer(initial_reveal_state, {
      type: "enqueue",
      item: heartbeat("h1"),
    });
    state = reveal_reducer(state, { type: "enqueue", item: markdown("a", "one") });
    state = reveal_reducer(state, { type: "enqueue", item: heartbeat("h2") });
    expect(state.pending.map((item) => item.message_id)).toEqual(["a"]);
    state = reveal_reducer(state, { type: "start" });
    expect(state.shown.map((item) => item.message_id)).toEqual(["a"]);
    expect(state.log.some((entry) => entry.kind === "agent" && entry.item.type === "heartbeat")).toBe(
      false,
    );
  });
});
