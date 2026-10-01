import { useEffect, useRef } from "react";

import { MicIcon, SendIcon } from "../shell/icons";
import { MessageView } from "./message_view";
import { Suggestions } from "./suggestions";
import type { use_chat_session } from "./use_chat_session";

import "./thread.css";

type Session = ReturnType<typeof use_chat_session>;

export function Thread({
  session,
  on_open_link,
}: {
  session: Session;
  on_open_link: (link: string, title?: string) => void;
}) {
  const { state, draft, set_draft, send, finish, timing } = session;
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
  return (
    <section
      className={empty ? "thread is-empty" : "thread"}
      aria-label="chat"
      ref={thread_ref}
    >
      {empty ? <h2 className="play-title">What's the play?</h2> : null}
      <div className="thread-viewport" ref={viewport_ref}>
        {state.log.map((entry) => {
          if (entry.kind === "user") {
            return (
              <p key={entry.id} className="message message-user">
                {entry.text}
              </p>
            );
          }
          return (
            <div key={entry.item.message_id} className="message message-assistant">
              <MessageView
                item={entry.item}
                active={entry.item.message_id === state.animating_id}
                timing={timing}
                on_done={finish}
                on_open_link={on_open_link}
              />
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
        <textarea
          className="composer-input"
          aria-label="Message"
          placeholder="Short $NVDA if chance of China-Taiwan war goes to over 90%"
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
        <div className="composer-tools">
          <span className="composer-mic" aria-hidden="true">
            <MicIcon />
          </span>
          <button
            type="submit"
            className="composer-send"
            aria-label="Send"
            disabled={state.running || draft.trim() === ""}
          >
            <SendIcon />
          </button>
        </div>
      </form>
      {empty ? <Suggestions on_pick={set_draft} /> : null}
    </section>
  );
}
