import { useEffect, useState } from "react";

import { parse_deeplink } from "../chain/deeplink";
import type { ChatItem } from "./chat_item";
import type { RevealTiming } from "./reveal_timing";

export function MessageView({
  item,
  active,
  timing,
  on_done,
  on_open_link,
}: {
  item: ChatItem;
  active: boolean;
  timing: RevealTiming;
  on_done: () => void;
  on_open_link: (link: string, title?: string) => void;
}) {
  switch (item.type) {
    case "markdown":
      return (
        <MarkdownReveal
          text={item.text}
          active={active}
          duration_ms={timing.markdown_ms(item.text)}
          on_done={on_done}
        />
      );
    case "deeplink":
      return <DeeplinkMessage item={item} on_open_link={on_open_link} />;
    case "heartbeat":
      return <HeartbeatMessage />;
  }
}

function MarkdownReveal({
  text,
  active,
  duration_ms,
  on_done,
}: {
  text: string;
  active: boolean;
  duration_ms: number;
  on_done: () => void;
}) {
  const [count, set_count] = useState(active ? 0 : text.length);
  useEffect(() => {
    if (!active) {
      set_count(text.length);
      return;
    }
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    if (reduce || duration_ms <= 0) {
      set_count(text.length);
      on_done();
      return;
    }
    const step_ms = 24;
    const steps = Math.max(1, Math.round(duration_ms / step_ms));
    let index = 0;
    const timer = window.setInterval(() => {
      index += 1;
      set_count(Math.ceil((text.length * Math.min(1, index / steps))));
      if (index >= steps) {
        window.clearInterval(timer);
        on_done();
      }
    }, step_ms);
    return () => window.clearInterval(timer);
  }, [active, duration_ms, on_done, text]);
  return <p className="agent-text">{text.slice(0, count)}</p>;
}

function DeeplinkMessage({
  item,
  on_open_link,
}: {
  item: Extract<ChatItem, { type: "deeplink" }>;
  on_open_link: (link: string, title?: string) => void;
}) {
  const parsed = parse_deeplink(item.link);
  const title =
    item.title ||
    (parsed?.route === "chain" ? parsed.title : "") ||
    (parsed === null ? item.link : "Open causal chain");
  const href =
    parsed === null
      ? item.link
      : parsed.route === "case" || parsed.route === "chain"
        ? "causal_chains://chain"
        : `causal_chains://${parsed.route}`;
  return (
    <button type="button" className="deeplink-card" onClick={() => on_open_link(item.link, item.title)}>
      <span className="deeplink-card-kicker">{href}</span>
      <span className="deeplink-card-title">{title || "Open causal chain"}</span>
    </button>
  );
}

function HeartbeatMessage() {
  return (
    <p className="heartbeat" role="status">
      <span className="heartbeat-dot" />
      working through the chain
    </p>
  );
}
