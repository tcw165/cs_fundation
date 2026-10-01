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
          'event: markdown\ndata: {"kind":"markdown","message_id":"m_1","role":"agent","text":"oil ","created_timestamp":"2026-09-30T00:00:00+00:00"}\n\n',
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
      abort_signal,
    })) {
      events.push(event);
    }
    expect(events).toEqual([
      {
        kind: "markdown",
        message_id: "m_1",
        role: "agent",
        text: "oil ",
        created_timestamp: "2026-09-30T00:00:00+00:00",
      },
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
        'down\ndata: {"kind":"markdown","message_id":"m_1","role":"agent","text":"oil ","created_timestamp":"2026-09-30T00:00:00+00:00"}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      {
        kind: "markdown",
        message_id: "m_1",
        role: "agent",
        text: "oil ",
        created_timestamp: "2026-09-30T00:00:00+00:00",
      },
    ]);
  });

  it("decodes a deeplink message", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream([
        'event: deeplink\ndata: {"kind":"deeplink","message_id":"m_card","role":"other","link":"/chain/11111111-1111-4111-8111-111111111111/1?title=now","created_timestamp":"2026-09-30T00:00:00+00:00"}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      {
        kind: "deeplink",
        created_timestamp: "2026-09-30T00:00:00+00:00",
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
        'event: heartbeat\ndata: {"kind":"heartbeat","role":"meta"}\n\n',
      ]),
    )) {
      events.push(event);
    }
    expect(events).toEqual([
      { kind: "heartbeat", role: "meta" },
    ]);
  });

  it("does not decode a payload that still says type", async () => {
    const stream = parse_sse_stream(
      sse_stream([
        'event: markdown\ndata: {"type":"markdown","message_id":"m_1","role":"agent","text":"oil ","created_timestamp":"2026-09-30T00:00:00+00:00"}\n\n',
      ]),
    );
    await expect(stream.next()).rejects.toThrow(/unknown sse event/);
  });
});
