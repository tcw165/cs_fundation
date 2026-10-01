// @vitest-environment jsdom

import type { ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { act } from "react";
import { describe, expect, it } from "vitest";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

import type { RevealTiming } from "./reveal_timing";
import { MessageView } from "./message_view";

const timing: RevealTiming = {
  markdown_ms: () => 0,
  deeplink_ms: 0,
  heartbeat_ms: 0,
};

const case_id = "c977e280-41f7-45e3-a33e-74c1d25c9156";

function render(node: ReactElement): { host: HTMLDivElement; root: Root } {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  act(() => {
    root.render(node);
  });
  return { host, root };
}

describe("deeplink card", () => {
  it("shows causal_chains://chain/<case_id>", () => {
    const { host, root } = render(
      <MessageView
        item={{
          type: "deeplink",
          message_id: "m",
          role: "other",
          title: "Strait of Hormuz Opening",
          link: `causal_chains://chain/${case_id}`,
        }}
        active={false}
        timing={timing}
        on_done={() => undefined}
        on_open_link={() => undefined}
      />,
    );
    expect(host.querySelector(".deeplink-card-kicker")?.textContent).toBe(
      `causal_chains://chain/${case_id}`,
    );
    act(() => {
      root.unmount();
    });
    host.remove();
  });
});
