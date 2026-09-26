import type { ChatPort, SseEvent, Turn } from "./chat_port";

export function create_chat_http(api_url: string): ChatPort {
  return {
    post_message: async ({ conversation_id, text, abort_signal }) => {
      const response = await fetch(
        `${api_url}/conversation/${conversation_id}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
          signal: abort_signal,
        },
      );
      if (!response.ok) {
        throw new Error(`post_message failed: ${response.status}`);
      }
      return (await response.json()) as Turn;
    },
    subscribe_turn: ({ conversation_id, turn_id, abort_signal }) => {
      return read_turn_sse(api_url, conversation_id, turn_id, abort_signal);
    },
  };
}

async function* read_turn_sse(
  api_url: string,
  conversation_id: string,
  turn_id: string,
  abort_signal?: AbortSignal,
): AsyncGenerator<SseEvent> {
  const response = await fetch(
    `${api_url}/conversation/${conversation_id}/turn/${turn_id}/sse`,
    { signal: abort_signal },
  );
  if (!response.ok || response.body === null) {
    throw new Error(`subscribe_turn failed: ${response.status}`);
  }
  yield* parse_sse_stream(response.body);
}

export async function* parse_sse_stream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<SseEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event_name = "";
  let data_lines: string[] = [];

  const flush = (): SseEvent | null => {
    const data = data_lines.join("\n");
    const name = event_name;
    event_name = "";
    data_lines = [];
    if (name === "" && data === "") {
      return null;
    }
    return decode_sse_event(name, data);
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      const lines = buffer.split(/\r?\n/);
      buffer = done ? "" : (lines.pop() ?? "");
      for (const line of lines) {
        if (line === "") {
          const event = flush();
          if (event !== null) {
            yield event;
          }
          continue;
        }
        if (line.startsWith(":")) {
          continue;
        }
        const separator = line.indexOf(":");
        const field = separator === -1 ? line : line.slice(0, separator);
        let field_value = separator === -1 ? "" : line.slice(separator + 1);
        if (field_value.startsWith(" ")) {
          field_value = field_value.slice(1);
        }
        if (field === "event") {
          event_name = field_value;
        } else if (field === "data") {
          data_lines.push(field_value);
        }
      }
      if (done) {
        const event = flush();
        if (event !== null) {
          yield event;
        }
        return;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function decode_sse_event(event_name: string, data: string): SseEvent {
  const payload = data === "" ? {} : (JSON.parse(data) as Record<string, string>);
  if (event_name === "delta") {
    return { type: "delta", text: payload.text ?? "" };
  }
  if (event_name === "tool") {
    return {
      type: "tool",
      name: payload.name ?? "",
      status: payload.status ?? "",
    };
  }
  if (event_name === "done") {
    return { type: "done", message_id: payload.message_id ?? "" };
  }
  if (event_name === "error") {
    return { type: "error", message: payload.message ?? "sse error" };
  }
  throw new Error(`unknown sse event: ${event_name}`);
}
