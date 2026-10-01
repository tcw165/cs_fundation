import { useEffect, useRef } from "react";

import { MicIcon, SendIcon } from "../shell/icons";
import { format_message_time, message_marks, type MessageMark } from "./message_time";
import { MessageView } from "./message_view";
import type { TranscriptEntry } from "./reveal_state";
import { Suggestions } from "./suggestions";
import type { use_chat_session } from "./use_chat_session";

import "./thread.css";

type Session = ReturnType<typeof use_chat_session>;

function entry_timestamp(entry: TranscriptEntry): string | null {
  if (entry.kind === "user") {
    return entry.created_timestamp;
  }
  if (entry.item.kind === "heartbeat") {
    return null;
  }
  return entry.item.created_timestamp;
}

function MessageTime({ created_timestamp }: { created_timestamp: string }) {
  return (
    <time className="message-time" dateTime={created_timestamp}>
      {format_message_time(created_timestamp)}
    </time>
  );
}

function earlier_timestamp(timestamps: Array<string | null>, index: number): string | null {
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    const earlier = timestamps[cursor];
    if (earlier !== null && earlier !== undefined) {
      return earlier;
    }
  }
  return null;
}

function followed_by_separator(
  marks: MessageMark[],
  timestamps: Array<string | null>,
  index: number,
): boolean {
  for (let cursor = index + 1; cursor < timestamps.length; cursor += 1) {
    if (timestamps[cursor] === null) {
      continue;
    }
    return marks[cursor]?.show_separator === true;
  }
  return false;
}

export function Thread({
  session,
  on_open_link,
}: {
  session: Session;
  on_open_link: (link: string, title?: string) => void;
}) {
  const { state, draft, set_draft, send, finish, timing, user_interaction_state, stop } =
    session;
  const send_disabled =
    user_interaction_state.text_input_state === "SEND_DISABLED" ||
    user_interaction_state.text_input_state === "DISABLED" ||
    user_interaction_state.text_input_state === "HIDDEN" ||
    draft.trim() === "";
  const empty = state.log.length === 0;
  const thread_ref = useRef<HTMLElement | null>(null);
  const viewport_ref = useRef<HTMLDivElement | null>(null);
  const composer_ref = useRef<HTMLFormElement | null>(null);
  useEffect(() => {
    const thread = thread_ref.current;
    const viewport = viewport_ref.current;
    const composer = composer_ref.current;
    if (thread === null || viewport === null || composer === null) {
      return;
    }
    const apply = () => {
      const bottom = 24;
      const gap = 16;
      const bar = viewport.offsetWidth - viewport.clientWidth;
      thread.style.setProperty("--scrollbar-size", `${bar}px`);
      thread.style.setProperty(
        "--composer-cover",
        `${composer.offsetHeight + bottom + gap}px`,
      );
    };
    apply();
    const observer = new ResizeObserver(apply);
    observer.observe(composer);
    observer.observe(viewport);
    return () => observer.disconnect();
  }, []);
  const timestamps = state.log.map(entry_timestamp);
  const marks = message_marks(timestamps);
  return (
    <section
      className={empty ? "thread is-empty" : "thread"}
      aria-label="chat"
      ref={thread_ref}
    >
      {empty ? <h2 className="play-title">What's the play?</h2> : null}
      <div className="thread-viewport" ref={viewport_ref}>
        {marks.map((mark, index) => {
          const entry = state.log[index];
          if (entry === undefined) {
            return null;
          }
          const timestamp = timestamps[index] ?? null;
          const time =
            mark?.show_timestamp === true &&
            timestamp !== null &&
            !followed_by_separator(marks, timestamps, index) ? (
              <MessageTime created_timestamp={timestamp} />
            ) : null;
          const divider_time =
            mark?.show_separator === true ? earlier_timestamp(timestamps, index) : null;
          const separator =
            mark?.show_separator === true ? (
              <div className="message-separator" role="separator">
                {divider_time !== null ? (
                  <time className="message-separator-time" dateTime={divider_time}>
                    {format_message_time(divider_time)}
                  </time>
                ) : null}
              </div>
            ) : null;
          if (entry.kind === "user") {
            return (
              <div key={entry.id}>
                {separator}
                <div className="message message-user">
                  <p>{entry.text}</p>
                  {time}
                </div>
              </div>
            );
          }
          return (
            <div key={entry.item.message_id}>
              {separator}
              <div className="message message-assistant">
                <MessageView
                  item={entry.item}
                  active={entry.item.message_id === state.animating_id}
                  timing={timing}
                  on_done={finish}
                  on_open_link={on_open_link}
                />
                {time}
              </div>
            </div>
          );
        })}
        {state.error !== null ? <p className="chat-error">{state.error}</p> : null}
      </div>
      <form
        className="composer"
        ref={composer_ref}
        onSubmit={(event) => {
          event.preventDefault();
          void send(draft);
        }}
      >
        {user_interaction_state.thinking_state === null ? null : (
          <p className="composer-thinking">{user_interaction_state.thinking_state.text}</p>
        )}
        {user_interaction_state.text_input_state === "HIDDEN" ? null : (
          <textarea
            className="composer-input"
            aria-label="Message"
            placeholder={user_interaction_state.text_input_placeholder}
            disabled={user_interaction_state.text_input_state === "DISABLED"}
            rows={3}
            value={draft}
            onChange={(event) => set_draft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send(draft);
              }
            }}
          />
        )}
        <div className="composer-tools">
          <span className="composer-mic" aria-hidden="true">
            <MicIcon />
          </span>
          <button
            type="submit"
            className="composer-send"
            aria-label="Send"
            disabled={send_disabled}
          >
            <SendIcon />
          </button>
          {user_interaction_state.text_input_state === "SEND_ENABLED_WITH_STOP_BUTTON" ? (
            <button type="button" aria-label="Stop" onClick={stop}>
              Stop
            </button>
          ) : null}
        </div>
      </form>
      {empty ? <Suggestions on_pick={set_draft} /> : null}
    </section>
  );
}
