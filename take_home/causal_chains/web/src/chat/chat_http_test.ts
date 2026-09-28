import { describe, expect, it, vi } from "vitest";

import { create_chat_http, parse_sse_stream } from "./chat_http";

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
          turn_id: "t_8f3a",
          conversation_id: "1",
          status: "queued",
          from_message: "m_user",
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        body: sse_stream([
          'event: markdown\ndata: {"message_id":"m_1","role":"agent","text":"oil "}\n\n',
        ]),
      });
    vi.stubGlobal("fetch", fetch_mock);
    const abort_signal = new AbortController().signal;
    const chat_port = create_chat_http("http://agents:8000");
    const turn = await chat_port.post_message({
      conversation_id: "1",
      text: "hello",
      abort_signal,
    });
    expect(turn).toEqual({
      turn_id: "t_8f3a",
      conversation_id: "1",
      status: "queued",
      from_message: "m_user",
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
      turn_id: turn.turn_id,
      after_message: turn.from_message,
      abort_signal,
    })) {
      events.push(event);
    }
    expect(events).toEqual([
      { type: "markdown", message_id: "m_1", role: "agent", text: "oil " },
    ]);
    expect(fetch_mock).toHaveBeenCalledWith(
      "http://agents:8000/conversation/1/turn/t_8f3a/sse?after_message=m_user",
      { signal: abort_signal },
    );
    vi.unstubAllGlobals();
  });
});

describe("parse_sse_stream", () => {
  it("reassembles events split across chunks", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream([
        'event: mark',
        'down\ndata: {"message_id":"m_1","role":"agent","text":"oil "}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      { type: "markdown", message_id: "m_1", role: "agent", text: "oil " },
    ]);
  });

  it("decodes a deeplink message", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream([
        'event: deeplink\ndata: {"message_id":"m_card","role":"other","link":"/chain/11111111-1111-4111-8111-111111111111/1?title=now"}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      {
        type: "deeplink",
        message_id: "m_card",
        role: "other",
        link: "/chain/11111111-1111-4111-8111-111111111111/1?title=now",
      },
    ]);
  });

  it("decodes a heartbeat the page does not render", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream([
        'event: heartbeat\ndata: {"message_id":"m_beat","role":"meta"}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      { type: "heartbeat", message_id: "m_beat", role: "meta" },
    ]);
  });
});
