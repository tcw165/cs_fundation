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
      const paragraphs: string[] = [];
      const cards: DeeplinkCard[] = [];
      for await (const event of chat_port.subscribe_turn({
        conversation_id,
        turn_id: turn.turn_id,
        after_message: turn.from_message,
        abort_signal: abortSignal,
      })) {
        if (event.type === "heartbeat") {
          continue;
        }
        if (event.type === "markdown" && event.role === "agent") {
          paragraphs.push(event.text);
          yield assistant_snapshot(paragraphs, cards);
        }
        if (event.type === "deeplink") {
          cards.push(card_from_link(event.link));
          yield assistant_snapshot(paragraphs, cards);
        }
      }
    },
  };
}

export function card_from_link(link: string): DeeplinkCard {
  const url = new URL(link, "http://local");
  const parts = url.pathname.split("/").filter((part) => part !== "");
  const root_version = Number(parts[2] ?? "0");
  return {
    title: url.searchParams.get("title") ?? "",
    root_situation_id: parts[1] ?? "",
    root_version: Number.isFinite(root_version) ? root_version : 0,
  };
}

function assistant_snapshot(paragraphs: string[], cards: DeeplinkCard[]) {
  const content: (
    | { type: "text"; text: string }
    | { type: "data"; name: "deeplink_widget"; data: DeeplinkCard }
  )[] = [];
  const text = paragraphs.join("\n\n");
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
