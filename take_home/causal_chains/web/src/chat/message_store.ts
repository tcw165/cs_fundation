import type { Message } from "./chat_port";

export type MessageStore = {
  remember: (message: Message) => boolean;
  messages: () => readonly Message[];
};

export function create_message_store(): MessageStore {
  const by_id = new Map<string, Message>();
  const ordered: Message[] = [];
  return {
    remember(message) {
      if (message.kind === "heartbeat" || message.message_id === undefined) {
        return true;
      }
      if (by_id.has(message.message_id)) {
        return false;
      }
      by_id.set(message.message_id, message);
      ordered.push(message);
      return true;
    },
    messages() {
      return ordered;
    },
  };
}
