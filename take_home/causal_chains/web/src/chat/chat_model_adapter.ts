import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";

import type { DeeplinkCard } from "../chain/chain_port";
import type { ChatPort } from "./chat_port";

export function create_chat_model_adapter(
  chat_port: ChatPort,
  conversation_id: string,
): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      const turn = await chat_port.post_message({
        conversation_id,
        text: last_user_text(messages),
        abort_signal: abortSignal,
      });
      let text = "";
      const cards: DeeplinkCard[] = [];
      for await (const event of chat_port.subscribe_turn({
        conversation_id,
        turn_id: turn.turn_id,
        abort_signal: abortSignal,
      })) {
        if (event.type === "delta") {
          text += event.text;
          yield assistant_snapshot(text, cards);
        }
        if (event.type === "deeplink_widget") {
          cards.push(event.card);
          yield assistant_snapshot(text, cards);
        }
        if (event.type === "done") {
          return;
        }
        if (event.type === "error") {
          throw new Error(event.message);
        }
      }
    },
  };
}

function assistant_snapshot(text: string, cards: DeeplinkCard[]) {
  const content: (
    | { type: "text"; text: string }
    | { type: "data"; name: "deeplink_widget"; data: DeeplinkCard }
  )[] = [];
  if (text !== "") {
    content.push({ type: "text", text });
  }
  for (const card of cards) {
    content.push({ type: "data", name: "deeplink_widget", data: card });
  }
  return { content };
}

export function last_user_text(messages: readonly ThreadMessage[]): string {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message === undefined || message.role !== "user") {
      continue;
    }
    const text = message.content
      .filter((part): part is { type: "text"; text: string } => part.type === "text")
      .map((part) => part.text)
      .join("");
    if (text !== "") {
      return text;
    }
  }
  return "";
}
