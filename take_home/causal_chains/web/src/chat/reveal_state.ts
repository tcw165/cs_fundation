import type { ChatItem } from "./chat_item";

export type RevealPhase = "idle" | "animating";

export type TranscriptEntry =
  | { kind: "user"; id: string; text: string }
  | { kind: "agent"; item: ChatItem };

export type RevealState = {
  user_texts: string[];
  pending: ChatItem[];
  shown: ChatItem[];
  log: TranscriptEntry[];
  phase: RevealPhase;
  animating_id: string | null;
  running: boolean;
  error: string | null;
};

export const initial_reveal_state: RevealState = {
  user_texts: [],
  pending: [],
  shown: [],
  log: [],
  phase: "idle",
  animating_id: null,
  running: false,
  error: null,
};

export type RevealAction =
  | { type: "user"; text: string }
  | { type: "enqueue"; item: ChatItem }
  | { type: "start" }
  | { type: "finish" }
  | { type: "run"; running: boolean }
  | { type: "error"; message: string };

export function reveal_reducer(state: RevealState, action: RevealAction): RevealState {
  switch (action.type) {
    case "user":
      return {
        ...state,
        user_texts: [...state.user_texts, action.text],
        log: [
          ...state.log,
          { kind: "user", id: `user-${state.user_texts.length}`, text: action.text },
        ],
        error: null,
      };
    case "enqueue":
      return enqueue_item(state, action.item);
    case "start": {
      if (state.phase === "animating" || state.pending.length === 0) {
        return state;
      }
      const [next, ...rest] = state.pending;
      if (next === undefined) {
        return state;
      }
      return {
        ...state,
        pending: rest,
        shown: [...state.shown, next],
        log: [...state.log, { kind: "agent", item: next }],
        phase: "animating",
        animating_id: next.message_id,
      };
    }
    case "finish":
      if (state.phase !== "animating") {
        return state;
      }
      return { ...state, phase: "idle", animating_id: null };
    case "run":
      return { ...state, running: action.running };
    case "error":
      return { ...state, error: action.message, running: false };
  }
}

function enqueue_item(state: RevealState, item: ChatItem): RevealState {
  if (item.type === "heartbeat") {
    const tail = state.pending[state.pending.length - 1];
    if (tail?.type === "heartbeat") {
      const pending = state.pending.slice();
      pending[pending.length - 1] = item;
      return { ...state, pending };
    }
    if (state.pending.length === 0 && state.phase === "animating") {
      const current = state.shown.find((shown) => shown.message_id === state.animating_id);
      if (current?.type === "heartbeat") {
        return state;
      }
    }
  }
  return { ...state, pending: [...state.pending, item] };
}
