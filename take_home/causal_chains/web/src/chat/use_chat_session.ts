import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { chat_item_from_message } from "./chat_item";
import type { ChatPort } from "./chat_port";
import { initial_reveal_state, reveal_reducer } from "./reveal_state";
import type { RevealTiming } from "./reveal_timing";

export function use_chat_session(
  chat_port: ChatPort,
  conversation_id: string,
  timing: RevealTiming,
) {
  const [state, dispatch] = useReducer(reveal_reducer, initial_reveal_state);
  const [draft, set_draft] = useState("");
  const running_ref = useRef(false);
  const finished_id = useRef<string | null>(null);

  useEffect(() => {
    if (state.phase === "idle" && state.pending.length > 0) {
      dispatch({ type: "start" });
    }
  }, [state.phase, state.pending.length]);

  const animating = state.shown.find((item) => item.message_id === state.animating_id) ?? null;

  const finish = useCallback(() => {
    if (
      state.animating_id != null &&
      finished_id.current === state.animating_id
    ) {
      return;
    }
    finished_id.current = state.animating_id;
    dispatch({ type: "finish" });
  }, [state.animating_id]);

  useEffect(() => {
    if (animating === null || animating.kind === "markdown") {
      return;
    }
    const ms = animating.kind === "deeplink" ? timing.deeplink_ms : timing.heartbeat_ms;
    const timer = window.setTimeout(() => finish(), ms);
    return () => window.clearTimeout(timer);
  }, [animating, finish, timing.deeplink_ms, timing.heartbeat_ms]);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (trimmed === "" || running_ref.current) {
        return;
      }
      running_ref.current = true;
      dispatch({ type: "user", text: trimmed });
      dispatch({ type: "run", running: true });
      set_draft("");
      try {
        const turn = await chat_port.post_message({
          conversation_id,
          text: trimmed,
        });
        for await (const message of chat_port.subscribe_turn({
          conversation_id,
          turn_id: turn.turn_id,
          after_message: turn.from_message,
        })) {
          dispatch({ type: "enqueue", item: chat_item_from_message(message) });
        }
      } catch (error) {
        dispatch({
          type: "error",
          message: error instanceof Error ? error.message : "send failed",
        });
      } finally {
        running_ref.current = false;
        dispatch({ type: "run", running: false });
      }
    },
    [chat_port, conversation_id],
  );

  return { state, draft, set_draft, send, finish, timing };
}
