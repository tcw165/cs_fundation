import { describe, expect, it, vi } from "vitest";

import { create_chat_http, parse_sse_stream } from "./chat_http";
import type { ConversationMessagesResponse, Message } from "./chat_port";

function page(messages: Message[]): ConversationMessagesResponse {
  return {
    conversation_id: "1",
    messages,
    user_interaction_state: {
      text_input_state: "SEND_ENABLED_WITH_STOP_BUTTON",
      text_input_placeholder: "Ask about a chain",
      thinking_state: null,
    },
    turn: null,
  };
}

function sse_stream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe("create_chat_http", () => {
  it("posts a message then subscribes with after_message", async () => {
    const fetch_mock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          turn: {
            turn_id: "t_8f3a",
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
      })
      .mockResolvedValueOnce({
        ok: true,
        body: sse_stream([
          `event: conversation_messages\ndata: ${JSON.stringify(page([{ kind: "markdown", message_id: "m_1", role: "agent", text: "oil ", created_timestamp: "2026-09-30T00:00:00+00:00" }]))}\n\n`,
        ]),
      });
    vi.stubGlobal("fetch", fetch_mock);
    const abort_signal = new AbortController().signal;
    const chat_port = create_chat_http("http://agents:8000");
    const posted = await chat_port.post_message({
      conversation_id: "1",
      text: "hello",
      abort_signal,
    });
    expect(posted.turn).toEqual({
      turn_id: "t_8f3a",
      conversation_id: "1",
      status: "queued",
      from_message: "m_user",
    });
    expect(posted.received_message).toMatchObject({
      kind: "markdown",
      message_id: "m_user",
      text: "hello",
    });
    expect(fetch_mock).toHaveBeenCalledWith(
      "http://agents:8000/conversation/1/messages",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "hello" }),
        signal: abort_signal,
      },
    );
    const events = [];
    for await (const event of chat_port.subscribe_turn({
      conversation_id: "1",
      turn_id: posted.turn.turn_id,
      after_message: posted.turn.from_message,
      after_message_timestamp: "2026-09-30T00:00:00+00:00",
      abort_signal,
    })) {
      events.push(event);
    }
    expect(events).toEqual([
      page([
        {
          kind: "markdown",
          message_id: "m_1",
          role: "agent",
          text: "oil ",
          created_timestamp: "2026-09-30T00:00:00+00:00",
        },
      ]),
    ]);
    expect(fetch_mock).toHaveBeenCalledWith(
      "http://agents:8000/conversation/1/turn/t_8f3a/sse?after_message=m_user&after_message_timestamp=2026-09-30T00%3A00%3A00%2B00%3A00",
      { signal: abort_signal },
    );
    vi.unstubAllGlobals();
  });

  it("reads one message page", async () => {
    const fetch_mock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        messages: [
          {
            kind: "markdown",
            message_id: "m_1",
            role: "user",
            text: "earlier",
            created_timestamp: "2026-09-30T00:00:00+00:00",
          },
        ],
        next_cursor: "MSG#1",
      }),
    });
    vi.stubGlobal("fetch", fetch_mock);
    const abort_signal = new AbortController().signal;
    const page = await create_chat_http("http://agents:8000").list_messages({
      conversation_id: "1",
      limit: 20,
      after_message: "MSG#0",
      after_message_timestamp: "2026-09-30T00:00:00+00:00",
      abort_signal,
    });
    expect(page.next_cursor).toBe("MSG#1");
    expect(page.messages[0]).toMatchObject({ message_id: "m_1", text: "earlier" });
    expect(fetch_mock).toHaveBeenCalledWith(
      "http://agents:8000/conversation/1/messages?limit=20&after_message=MSG%230&after_message_timestamp=2026-09-30T00%3A00%3A00%2B00%3A00",
      { signal: abort_signal },
    );
    vi.unstubAllGlobals();
  });
});

describe("parse_sse_stream", () => {
  it("yields a heartbeat from one conversation_messages event", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream([
        `event: conversation_messages\ndata: ${JSON.stringify(page([{ kind: "heartbeat", role: "meta" }]))}\n\n`,
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([page([{ kind: "heartbeat", role: "meta" }])]);
    expect(events[0]?.messages).toEqual([{ kind: "heartbeat", role: "meta" }]);
  });

  it("yields only the markdown message in that event", async () => {
    const message: Message = {
      kind: "markdown",
      message_id: "m_1",
      role: "agent",
      text: "oil ",
      created_timestamp: "2026-09-30T00:00:00+00:00",
    };
    const events = [];
    const payload = JSON.stringify(page([message]));
    for await (const event of parse_sse_stream(
      sse_stream([`event: conversation_mess`, `ages\ndata: ${payload}\n\n`]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([page([message])]);
    expect(events[0]?.messages).toEqual([message]);
  });

  it("rejects an unknown event name", async () => {
    const stream = parse_sse_stream(
      sse_stream(['event: markdown\ndata: {"kind":"markdown"}\n\n']),
    );
    await expect(stream.next()).rejects.toThrow(/unknown sse event/);
  });
});
