import type { ChatModelRunOptions, ThreadMessage } from "@assistant-ui/react";
import { describe, expect, it } from "vitest";

import { create_chat_model_adapter } from "./chat_model_adapter";
import type { ChatPort, SseEvent } from "./chat_port";

function user_message(text: string): ThreadMessage {
  return {
    id: "m_user",
    createdAt: new Date(0),
    role: "user",
    content: [{ type: "text", text }],
    attachments: [],
    metadata: { custom: {} },
  };
}

describe("create_chat_model_adapter", () => {
  it("posts then yields cumulative assistant snapshots", async () => {
    const posted: string[] = [];
    const chat_port: ChatPort = {
      post_message: async ({ text }) => {
        posted.push(text);
        return {
          turn_id: "t_1",
          conversation_id: "1",
          status: "queued",
        };
      },
      subscribe_turn: async function* (): AsyncGenerator<SseEvent> {
        yield { type: "delta", text: "oil " };
        yield { type: "tool", name: "ground", status: "called" };
        yield { type: "delta", text: "shock" };
        yield { type: "done", message_id: "m_1" };
      },
    };
    const adapter = create_chat_model_adapter(chat_port, "1");
    const snapshots = [];
    const run = adapter.run({
      messages: [user_message("hello")],
      abortSignal: new AbortController().signal,
    } as unknown as ChatModelRunOptions);
    for await (const snapshot of run as AsyncGenerator<{
      content: { type: string; text: string }[];
    }>) {
      snapshots.push(snapshot);
    }
    expect(posted).toEqual(["hello"]);
    expect(snapshots).toEqual([
      { content: [{ type: "text", text: "oil " }] },
      { content: [{ type: "text", text: "oil shock" }] },
    ]);
  });

  it("throws when the turn stream reports an error", async () => {
    const chat_port: ChatPort = {
      post_message: async () => ({
        turn_id: "t_err",
        conversation_id: "1",
        status: "queued",
      }),
      subscribe_turn: async function* (): AsyncGenerator<SseEvent> {
        yield { type: "error", message: "boom" };
      },
    };
    const adapter = create_chat_model_adapter(chat_port, "1");
    const run = adapter.run({
      messages: [user_message("hello")],
      abortSignal: new AbortController().signal,
    } as unknown as ChatModelRunOptions);
    await expect(async () => {
      for await (const _snapshot of run as AsyncGenerator<unknown>) {
        // drain
      }
    }).rejects.toThrow("boom");
  });
});
