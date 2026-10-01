import type { Message, Role } from "./chat_port";

let heartbeat_serial = 0;

function heartbeat_message_id(message_id: string | undefined): string {
  if (message_id) {
    return message_id;
  }
  heartbeat_serial += 1;
  return `heartbeat-${heartbeat_serial}`;
}

export type ChatItem =
  | {
      kind: "markdown";
      message_id: string;
      role: Role;
      text: string;
      created_timestamp: string;
    }
  | {
      kind: "deeplink";
      message_id: string;
      role: Role;
      link: string;
      created_timestamp: string;
      title?: string;
    }
  | {
      kind: "heartbeat";
      message_id: string;
      role: "meta";
    };

export function chat_item_from_message(message: Message): ChatItem {
  switch (message.kind) {
    case "markdown":
      return {
        kind: "markdown",
        message_id: message.message_id,
        role: message.role,
        text: message.text,
        created_timestamp: message.created_timestamp,
      };
    case "deeplink":
      return {
        kind: "deeplink",
        message_id: message.message_id,
        role: message.role,
        link: message.link,
        created_timestamp: message.created_timestamp,
        ...(message.title === undefined ? {} : { title: message.title }),
      };
    case "heartbeat":
      return {
        kind: "heartbeat",
        message_id: heartbeat_message_id(message.message_id),
        role: "meta",
      };
  }
}
