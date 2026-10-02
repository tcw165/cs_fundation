import type { ChatModelRunOptions, ThreadMessage } from "@assistant-ui/react";
import { describe, expect, it } from "vitest";

import { create_chat_model_adapter } from "./chat_model_adapter";
import type { ChatPort, ConversationMessagesResponse, Message } from "./chat_port";

function page(messages: Message[]): ConversationMessagesResponse {
  return {
    conversation_id: "1",
    messages,
    user_interaction_state: {
      text_input_state: "SEND_ENABLED_WITH_STOP_BUTTON",
      text_input_placeholder: "Ask about a chain",
      thinking_state: null,
    },
    turn: { processing: [], queued: [] },
  };
}

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
  it("subscribes after the posted message and yields each agent paragraph", async () => {
    const posted: string[] = [];
    const turn_ids: string[] = [];
    const chat_port: ChatPort = {
      post_message: async ({ text }) => {
        posted.push(text);
        return {
          turn: {
            turn_id: "t_1",
            conversation_id: "1",
            status: "queued",
            from_message: "m_user",
          },
          received_message: {
            kind: "markdown",
            message_id: "m_user",
            role: "user",
            text,
            created_timestamp: "2026-09-30T00:00:00+00:00",
          },
        };
      },
      list_messages: async () => ({ messages: [], next_cursor: null }),
      subscribe_turn: async function* (req): AsyncGenerator<ConversationMessagesResponse> {
        turn_ids.push(req.turn_id);
        expect(req.after_message).toBe("m_user");
        yield page([
          {
            kind: "markdown",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_a",
            role: "agent",
            text: "one",
          },
          { kind: "heartbeat", role: "meta" },
          {
            kind: "markdown",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_b",
            role: "agent",
            text: "two",
          },
        ]);
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
    expect(turn_ids).toEqual(["t_1"]);
    expect(snapshots).toEqual([
      { content: [{ type: "text", text: "one" }] },
      { content: [{ type: "text", text: "one\n\ntwo" }] },
    ]);
  });

  it("parses a deeplink link into a card", async () => {
    const card = {
      title: "now",
      root_situation_id: "11111111-1111-4111-8111-111111111111",
      root_version: 1,
    };
    const chat_port: ChatPort = {
      post_message: async () => ({
        turn: {
          turn_id: "t_1",
          conversation_id: "1",
          status: "queued",
          from_message: "m_user",
        },
        received_message: {
          kind: "markdown",
          message_id: "m_user",
          role: "user",
          text: "hello",
          created_timestamp: "2026-09-30T00:00:00+00:00",
        },
      }),
      list_messages: async () => ({ messages: [], next_cursor: null }),
      subscribe_turn: async function* (): AsyncGenerator<ConversationMessagesResponse> {
        yield page([
          {
            kind: "markdown",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_a",
            role: "agent",
            text: "saved",
          },
          {
            kind: "deeplink",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_card",
            role: "other",
            link: "/chain/11111111-1111-4111-8111-111111111111/1?title=now",
          },
        ]);
      },
    };
    const adapter = create_chat_model_adapter(chat_port, "1");
    const snapshots = [];
    const run = adapter.run({
      messages: [user_message("hello")],
      abortSignal: new AbortController().signal,
    } as unknown as ChatModelRunOptions);
    for await (const snapshot of run as AsyncGenerator<{
      content: { type: string; text?: string; name?: string; data?: typeof card }[];
    }>) {
      snapshots.push(snapshot);
    }
    expect(snapshots).toEqual([
      { content: [{ type: "text", text: "saved" }] },
      {
        content: [
          { type: "text", text: "saved" },
          { type: "data", name: "deeplink_widget", data: card },
        ],
      },
    ]);
  });

  it("parses a causal_chains:// chain link", async () => {
    const chat_port: ChatPort = {
      post_message: async () => ({
        turn: {
          turn_id: "t_1",
          conversation_id: "1",
          status: "queued",
          from_message: "m_user",
        },
        received_message: {
          kind: "markdown",
          message_id: "m_user",
          role: "user",
          text: "hello",
          created_timestamp: "2026-09-30T00:00:00+00:00",
        },
      }),
      list_messages: async () => ({ messages: [], next_cursor: null }),
      subscribe_turn: async function* (): AsyncGenerator<ConversationMessagesResponse> {
        yield page([
          {
            kind: "deeplink",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_card",
            role: "other",
            link: "causal_chains://chain?root_situation_id=11111111-1111-4111-8111-111111111111&root_version=1&title=now",
          },
        ]);
      },
    };
    const adapter = create_chat_model_adapter(chat_port, "1");
    const snapshots = [];
    const run = adapter.run({
      messages: [user_message("hello")],
      abortSignal: new AbortController().signal,
    } as unknown as ChatModelRunOptions);
    for await (const snapshot of run as AsyncGenerator<{
      content: { type: string; data?: { root_situation_id: string; title: string } }[];
    }>) {
      snapshots.push(snapshot);
    }
    expect(snapshots[0]?.content[0]).toMatchObject({
      type: "data",
      data: {
        title: "now",
        root_situation_id: "11111111-1111-4111-8111-111111111111",
        root_version: 1,
      },
    });
  });

  it("finishes the turn when the stream ends", async () => {
    const chat_port: ChatPort = {
      post_message: async () => ({
        turn: {
          turn_id: "t_1",
          conversation_id: "1",
          status: "queued",
          from_message: "m_user",
        },
        received_message: {
          kind: "markdown",
          message_id: "m_user",
          role: "user",
          text: "hello",
          created_timestamp: "2026-09-30T00:00:00+00:00",
        },
      }),
      list_messages: async () => ({ messages: [], next_cursor: null }),
      subscribe_turn: async function* (): AsyncGenerator<ConversationMessagesResponse> {
        yield page([
          {
            kind: "markdown",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_a",
            role: "agent",
            text: "done talking",
          },
        ]);
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
    expect(snapshots).toEqual([
      { content: [{ type: "text", text: "done talking" }] },
    ]);
  });
});
