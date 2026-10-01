import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { chat_item_from_message } from "./chat_item";
import type { ChatPort, Message, UserInteractionState } from "./chat_port";
import { create_message_store } from "./message_store";
import { initial_reveal_state, reveal_reducer } from "./reveal_state";
import type { RevealTiming } from "./reveal_timing";

const NVDA_PLACEHOLDER =
  "Short $NVDA if chance of China-Taiwan war goes to over 90%";

const PAGE_LIMIT = 20;

const idle_interaction: UserInteractionState = {
  text_input_state: "ENABLED",
  text_input_placeholder: NVDA_PLACEHOLDER,
  thinking_state: null,
};

export function use_chat_session(
  chat_port: ChatPort,
  conversation_id: string,
  timing: RevealTiming,
) {
  const [state, dispatch] = useReducer(reveal_reducer, initial_reveal_state);
  const [draft, set_draft] = useState("");
  const [user_interaction_state, set_user_interaction_state] =
    useState<UserInteractionState>(idle_interaction);
  const running_ref = useRef(false);
  const abort_ref = useRef<AbortController | null>(null);
  const finished_id = useRef<string | null>(null);
  const messages_ref = useRef(create_message_store());

  useEffect(() => {
    if (state.phase === "idle" && state.pending.length > 0) {
      dispatch({ type: "start" });
    }
  }, [state.phase, state.pending.length]);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    async function load_history() {
      let cursor: string | undefined;
      do {
        const page = await chat_port.list_messages({
          conversation_id,
          limit: PAGE_LIMIT,
          cursor,
          abort_signal: controller.signal,
        });
        if (cancelled) {
          return;
        }
        for (const message of page.messages) {
          present_history(message);
        }
        cursor = page.next_cursor ?? undefined;
      } while (cursor !== undefined);
    }
    function present_history(message: Message) {
      if (!messages_ref.current.remember(message)) {
        return;
      }
      dispatch({ type: "restore", item: chat_item_from_message(message) });
    }
    void load_history().catch((error: unknown) => {
      if (cancelled || (error instanceof DOMException && error.name === "AbortError")) {
        return;
      }
      dispatch({
        type: "error",
        message: error instanceof Error ? error.message : "load failed",
      });
    });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [chat_port, conversation_id]);

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
      const controller = new AbortController();
      abort_ref.current = controller;
      dispatch({ type: "user", text: trimmed });
      dispatch({ type: "run", running: true });
      set_draft("");
      try {
        const posted = await chat_port.post_message({
          conversation_id,
          text: trimmed,
          abort_signal: controller.signal,
        });
        messages_ref.current.remember(posted.received_message);
        for await (const snapshot of chat_port.subscribe_turn({
          conversation_id,
          turn_id: posted.turn.turn_id,
          abort_signal: controller.signal,
        })) {
          set_user_interaction_state(snapshot.user_interaction_state);
          for (const message of snapshot.messages) {
            if (!messages_ref.current.remember(message)) {
              continue;
            }
            dispatch({ type: "enqueue", item: chat_item_from_message(message) });
          }
        }
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        dispatch({
          type: "error",
          message: error instanceof Error ? error.message : "send failed",
        });
      } finally {
        abort_ref.current = null;
        running_ref.current = false;
        dispatch({ type: "run", running: false });
      }
    },
    [chat_port, conversation_id],
  );

  const stop = useCallback(() => {
    abort_ref.current?.abort();
  }, []);

  return { state, draft, set_draft, send, finish, timing, user_interaction_state, stop };
}
