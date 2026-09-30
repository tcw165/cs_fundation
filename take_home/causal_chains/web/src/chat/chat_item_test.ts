import { describe, expect, it } from "vitest";

import { chat_item_from_message } from "./chat_item";
import type { Message } from "./chat_port";

describe("chat_item_from_message", () => {
  it("keeps each backend message type", () => {
    const messages: Message[] = [
      { type: "markdown", message_id: "m1", role: "agent", text: "one" },
      { type: "deeplink", message_id: "m2", role: "other", link: "causal_chains://chain?root_situation_id=a&root_version=1" },
      { type: "heartbeat", message_id: "m3", role: "meta" },
    ];
    expect(messages.map(chat_item_from_message)).toEqual([
      { type: "markdown", message_id: "m1", role: "agent", text: "one" },
      {
        type: "deeplink",
        message_id: "m2",
        role: "other",
        link: "causal_chains://chain?root_situation_id=a&root_version=1",
      },
      { type: "heartbeat", message_id: "m3", role: "meta" },
    ]);
  });

  it("gives each heartbeat without an id its own message id", () => {
    const first = chat_item_from_message({ type: "heartbeat", role: "meta" });
    const second = chat_item_from_message({ type: "heartbeat", role: "meta" });
    expect(first.message_id).toBeTruthy();
    expect(second.message_id).toBeTruthy();
    expect(first.message_id).not.toBe(second.message_id);
  });
});
