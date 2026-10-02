import type {
  ChatPort,
  ConversationMessagesResponse,
  MessagePage,
  PostMessageResponse,
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
      return (await response.json()) as PostMessageResponse;
    },
    list_messages: ({
      conversation_id,
      limit,
      after_message,
      after_message_timestamp,
      abort_signal,
    }) => {
      return read_message_page(
        api_url,
        conversation_id,
        limit,
        after_message,
        after_message_timestamp,
        abort_signal,
      );
    },
    subscribe_turn: ({
      conversation_id,
      turn_id,
      after_message,
      after_message_timestamp,
      abort_signal,
    }) => {
      return read_turn_sse(
        api_url,
        conversation_id,
        turn_id,
        after_message,
        after_message_timestamp,
        abort_signal,
      );
    },
  };
}

async function read_message_page(
  api_url: string,
  conversation_id: string,
  limit: number,
  after_message: string | undefined,
  after_message_timestamp: string | undefined,
  abort_signal?: AbortSignal,
): Promise<MessagePage> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (after_message !== undefined) {
    params.set("after_message", after_message);
  }
  if (after_message_timestamp !== undefined) {
    params.set("after_message_timestamp", after_message_timestamp);
  }
  const response = await fetch(
    `${api_url}/conversation/${conversation_id}/messages?${params}`,
    { signal: abort_signal },
  );
  if (!response.ok) {
    throw new Error(`list_messages failed: ${response.status}`);
  }
  return (await response.json()) as MessagePage;
}

async function* read_turn_sse(
  api_url: string,
  conversation_id: string,
  turn_id: string,
  after_message: string,
  after_message_timestamp: string,
  abort_signal?: AbortSignal,
): AsyncGenerator<ConversationMessagesResponse> {
  const params = new URLSearchParams({ after_message, after_message_timestamp });
  const response = await fetch(
    `${api_url}/conversation/${conversation_id}/turn/${turn_id}/sse?${params}`,
    { signal: abort_signal },
  );
  if (!response.ok || response.body === null) {
    throw new Error(`subscribe_turn failed: ${response.status}`);
  }
  yield* parse_sse_stream(response.body);
}

export async function* parse_sse_stream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<ConversationMessagesResponse> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let event_name = "";
  let data_lines: string[] = [];

  const flush = (): ConversationMessagesResponse | null => {
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

function decode_sse_event(
  event_name: string,
  data: string,
): ConversationMessagesResponse {
  if (event_name !== "conversation_messages") {
    throw new Error(`unknown sse event: ${event_name}`);
  }
  return JSON.parse(data) as ConversationMessagesResponse;
}
