import type {
  ChatPort,
  Message,
  Role,
  Turn,
} from "./chat_port";

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
    subscribe_turn: ({ conversation_id, turn_id, after_message, abort_signal }) => {
      return read_turn_sse(
        api_url,
        conversation_id,
        turn_id,
        after_message,
        abort_signal,
      );
    },
  };
}

async function* read_turn_sse(
  api_url: string,
  conversation_id: string,
  turn_id: string,
  after_message: string,
  abort_signal?: AbortSignal,
): AsyncGenerator<Message> {
  const query = new URLSearchParams({ after_message });
  const response = await fetch(
    `${api_url}/conversation/${conversation_id}/turn/${turn_id}/sse?${query}`,
    { signal: abort_signal },
  );
  if (!response.ok || response.body === null) {
    throw new Error(`subscribe_turn failed: ${response.status}`);
  }
  yield* parse_sse_stream(response.body);
}

export async function* parse_sse_stream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<Message> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event_name = "";
  let data_lines: string[] = [];

  const flush = (): Message | null => {
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

function text_field(
  payload: Record<string, unknown>,
  key: string,
  fallback = "",
): string {
  const value = payload[key];
  return typeof value === "string" ? value : fallback;
}

function role_field(payload: Record<string, unknown>): Role {
  const role = payload.role;
  if (role === "user" || role === "agent" || role === "other" || role === "meta") {
    return role;
  }
  return "other";
}

function decode_sse_event(event_name: string, data: string): Message {
  const payload =
    data === "" ? {} : (JSON.parse(data) as Record<string, unknown>);
  if (event_name === "markdown") {
    return {
      type: "markdown",
      message_id: text_field(payload, "message_id"),
      role: role_field(payload),
      text: text_field(payload, "text"),
    };
  }
  if (event_name === "deeplink") {
    const title = text_field(payload, "title");
    return {
      type: "deeplink",
      message_id: text_field(payload, "message_id"),
      role: role_field(payload),
      link: text_field(payload, "link"),
      ...(title === "" ? {} : { title }),
    };
  }
  if (event_name === "heartbeat") {
    return {
      type: "heartbeat",
      role: "meta",
    };
  }
  throw new Error(`unknown sse event: ${event_name}`);
}
