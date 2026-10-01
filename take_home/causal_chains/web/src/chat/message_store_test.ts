import { describe, expect, it } from "vitest";

import type { Message } from "./chat_port";
import { create_message_store } from "./message_store";

function markdown(message_id: string, text: string): Message {
  return {
    kind: "markdown",
    message_id,
    role: "agent",
    text,
    created_timestamp: "2026-09-30T00:00:00+00:00",
  };
}

describe("create_message_store", () => {
  it("keeps the first copy of a message id", () => {
    const store = create_message_store();
    expect(store.remember(markdown("m_a", "one"))).toBe(true);
    expect(store.remember(markdown("m_a", "one again"))).toBe(false);
    expect(store.remember(markdown("m_b", "two"))).toBe(true);
    expect(store.messages().map((message) => message.message_id)).toEqual(["m_a", "m_b"]);
  });

  it("lets every heartbeat through without storing it", () => {
    const store = create_message_store();
    expect(store.remember({ kind: "heartbeat", role: "meta" })).toBe(true);
    expect(store.remember({ kind: "heartbeat", role: "meta", message_id: "m_h" })).toBe(true);
    expect(store.remember({ kind: "heartbeat", role: "meta", message_id: "m_h" })).toBe(true);
    expect(store.messages()).toEqual([]);
  });
});
