// @vitest-environment jsdom

import type { ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { act } from "react";
import { describe, expect, it } from "vitest";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

import type { ChainPort } from "../chain/chain_port";
import type { ChatPort, Message } from "../chat/chat_port";
import type { RevealTiming } from "../chat/reveal_timing";
import { App } from "./app";

const now_id = "11111111-1111-4111-8111-111111111111";

const quick_timing: RevealTiming = {
  markdown_ms: () => 0,
  deeplink_ms: 50,
  heartbeat_ms: 50,
};

function render(node: ReactElement): { host: HTMLDivElement; root: Root } {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  act(() => {
    root.render(node);
  });
  return { host, root };
}

describe("app chat", () => {
  it("keeps the panel folded until a deeplink is ready", async () => {
    const chat_port: ChatPort = {
      post_message: async () => ({
        turn_id: "t_1",
        conversation_id: "1",
        status: "queued",
        from_message: "m_user",
      }),
      subscribe_turn: async function* (): AsyncGenerator<Message> {
        yield {
          kind: "markdown",
          created_timestamp: "2026-09-30T00:00:00+00:00",
          message_id: "m_a",
          role: "agent",
          text: "creating a case",
        };
        yield { kind: "heartbeat", message_id: "m_h", role: "meta" };
        yield {
          kind: "deeplink",
          created_timestamp: "2026-09-30T00:00:00+00:00",
          message_id: "m_d",
          role: "other",
          link: `causal_chains://chain?root_situation_id=${now_id}&root_version=1&title=now`,
        };
      },
    };
    const chain_port: ChainPort = {
      get_chains: async () => [
        {
          situations: [
            {
              situation_id: now_id,
              version: 1,
              desc: "strait shut",
              potential_factors: ["blockade"],
            },
          ],
          links: [],
        },
      ],
    };
    const { host, root } = render(
      <App
        chain_port={chain_port}
        chat_port={chat_port}
        conversation_id="1"
        timing={quick_timing}
      />,
    );
    expect(host.querySelector(".chain-canvas")).toBeNull();
    expect(host.textContent).toContain("What's the play?");
    const input = host.querySelector("textarea");
    await act(async () => {
      if (input instanceof HTMLTextAreaElement) {
        const setter = Object.getOwnPropertyDescriptor(
          window.HTMLTextAreaElement.prototype,
          "value",
        )?.set;
        setter?.call(input, "open the strait");
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await act(async () => {
      host
        .querySelector("form")
        ?.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      await Promise.resolve();
    });
    expect(host.textContent).toContain("creating a case");
    expect(host.textContent).toContain("working through the chain");
    expect(host.querySelector(".chain-canvas")).toBeNull();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 80));
    });
    expect(host.textContent).toContain("working through the chain");
    expect(host.textContent).toContain("causal_chains://chain");
    expect(host.querySelector(".chain-canvas")).not.toBeNull();
    expect(host.textContent).toContain("strait shut");
    act(() => {
      root.unmount();
    });
    host.remove();
  });
});
