export type Role = "user" | "agent" | "other" | "meta";

export type Turn = {
  turn_id: string;
  conversation_id: string;
  status: string;
  from_message: string;
};

export type MarkdownMessage = {
  type: "markdown";
  message_id: string;
  role: Role;
  text: string;
};

export type DeeplinkCardMessage = {
  type: "deeplink";
  message_id: string;
  role: Role;
  link: string;
  title?: string;
};

export type HeartbeatMessage = {
  type: "heartbeat";
  role: "meta";
};

export type Message = MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage;

export type PostMessageReq = {
  conversation_id: string;
  text: string;
  abort_signal?: AbortSignal;
};

export type SubscribeReq = {
  conversation_id: string;
  turn_id: string;
  after_message: string;
  abort_signal?: AbortSignal;
};

export type ChatPort = {
  post_message: (req: PostMessageReq) => Promise<Turn>;
  subscribe_turn: (req: SubscribeReq) => AsyncIterable<Message>;
};
