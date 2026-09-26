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
  it("posts a message then subscribes to turn sse", async () => {
    const fetch_mock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          turn_id: "t_8f3a",
          conversation_id: "1",
          status: "queued",
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        body: sse_stream([
          'event: delta\ndata: {"text":"oil "}\n\n',
          'event: done\ndata: {"message_id":"m_1"}\n\n',
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
      abort_signal,
    })) {
      events.push(event);
    }
    expect(events).toEqual([
      { type: "delta", text: "oil " },
      { type: "done", message_id: "m_1" },
    ]);
    expect(fetch_mock).toHaveBeenCalledWith(
      "http://agents:8000/conversation/1/turn/t_8f3a/sse",
      { signal: abort_signal },
    );
    vi.unstubAllGlobals();
  });
});

describe("parse_sse_stream", () => {
  it("reassembles events split across chunks", async () => {
    const events = [];
    for await (const event of parse_sse_stream(
      sse_stream(['event: del', 'ta\ndata: {"text":"oil "}\n\n']),
    )) {
      events.push(event);
    }
    expect(events).toEqual([{ type: "delta", text: "oil " }]);
  });
});
