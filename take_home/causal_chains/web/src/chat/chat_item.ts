import type { Message, Role } from "./chat_port";

export type ChatItem =
  | {
      type: "markdown";
      message_id: string;
      role: Role;
      text: string;
    }
  | {
      type: "deeplink";
      message_id: string;
      role: Role;
      link: string;
      title?: string;
    }
  | {
      type: "heartbeat";
      message_id: string;
      role: "meta";
    };

export function chat_item_from_message(message: Message): ChatItem {
  switch (message.type) {
    case "markdown":
      return {
        type: "markdown",
        message_id: message.message_id,
        role: message.role,
        text: message.text,
      };
    case "deeplink":
      return {
        type: "deeplink",
        message_id: message.message_id,
        role: message.role,
        link: message.link,
        ...(message.title === undefined ? {} : { title: message.title }),
      };
    case "heartbeat":
      return {
        type: "heartbeat",
        message_id: message.message_id,
        role: "meta",
      };
  }
}
