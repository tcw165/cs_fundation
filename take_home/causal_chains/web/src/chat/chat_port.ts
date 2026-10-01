export type Role = "user" | "agent" | "other" | "meta";

export type Turn = {
  turn_id: string;
  conversation_id: string;
  status: string;
  from_message: string;
};

export type MarkdownMessage = {
  kind: "markdown";
  message_id: string;
  role: Role;
  text: string;
  created_timestamp: string;
};

export type DeeplinkCardMessage = {
  kind: "deeplink";
  message_id: string;
  role: Role;
  link: string;
  created_timestamp: string;
  title?: string;
};

export type HeartbeatMessage = {
  kind: "heartbeat";
  role: "meta";
  message_id?: string;
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

export type PostMessageResponse = {
  turn: Turn;
  received_message: Message;
};

export type ChatPort = {
  post_message: (req: PostMessageReq) => Promise<PostMessageResponse>;
  subscribe_turn: (req: SubscribeReq) => AsyncIterable<Message>;
};
