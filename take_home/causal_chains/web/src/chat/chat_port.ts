export type Turn = {
  turn_id: string;
  conversation_id: string;
  status: string;
};

export type SseDelta = { type: "delta"; text: string };
export type SseTool = { type: "tool"; name: string; status: string };
export type SseDone = { type: "done"; message_id: string };
export type SseError = { type: "error"; message: string };
export type SseEvent = SseDelta | SseTool | SseDone | SseError;

export type PostMessageReq = {
  conversation_id: string;
  text: string;
  abort_signal?: AbortSignal;
};

export type SubscribeReq = {
  conversation_id: string;
  turn_id: string;
  abort_signal?: AbortSignal;
};

export type ChatPort = {
  post_message: (req: PostMessageReq) => Promise<Turn>;
  subscribe_turn: (req: SubscribeReq) => AsyncIterable<SseEvent>;
};
