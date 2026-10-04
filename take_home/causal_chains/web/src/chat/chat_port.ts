export type Role = "user" | "agent" | "other" | "meta" | "system";

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

export type SystemMessage = {
  kind: "system";
  message_id: string;
  role: "system";
  text: string;
  created_timestamp: string;
};

export type HeartbeatMessage = {
  kind: "heartbeat";
  role: "meta";
  message_id?: string;
};

export type Message = MarkdownMessage | DeeplinkCardMessage | SystemMessage | HeartbeatMessage;

export type PostMessageReq = {
  conversation_id: string;
  text: string;
  abort_signal?: AbortSignal;
};

export type SubscribeReq = {
  conversation_id: string;
  turn_id: string;
  after_message?: string;
  after_message_timestamp?: string;
  abort_signal?: AbortSignal;
};

export type TextInputState =
  | "ENABLED"
  | "SEND_DISABLED"
  | "SEND_ENABLED_WITH_STOP_BUTTON"
  | "DISABLED"
  | "HIDDEN";

export type ThinkingState = {
  text: string;
};

export type UserInteractionState = {
  text_input_state: TextInputState;
  text_input_placeholder: string;
  thinking_state: ThinkingState | null;
};

export type TurnDescriptor = {
  processing: Turn[];
  queued: Turn[];
};

export type CausalChainCase = {
  kind: "causal_chain_case";
  case_id: string;
  from_message_id: string;
};

export type LinkedConversation = {
  kind: "linked_conversation";
  conversation_id: string;
};

export type PeripheralInteraction = CausalChainCase | LinkedConversation;

export type ConversationMessagesResponse = {
  conversation_id: string;
  messages: Message[];
  user_interaction_state: UserInteractionState;
  turn: TurnDescriptor | null;
  peripheral_interactions?: PeripheralInteraction[];
};

export type PostMessageResponse = {
  turn: Turn;
  received_message: Message;
};

export type MessagePage = {
  messages: Message[];
  next_cursor: string | null;
};

export type ListMessagesReq = {
  conversation_id: string;
  limit: number;
  after_message?: string;
  after_message_timestamp?: string;
  abort_signal?: AbortSignal;
};

export type StopTurnReq = {
  conversation_id: string;
  turn_id: string;
};

export type ChatPort = {
  post_message: (req: PostMessageReq) => Promise<PostMessageResponse>;
  subscribe_turn: (req: SubscribeReq) => AsyncIterable<ConversationMessagesResponse>;
  list_messages: (req: ListMessagesReq) => Promise<MessagePage>;
  stop_turn: (req: StopTurnReq) => Promise<Turn>;
};
