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
import type { ChatPort, ConversationMessagesResponse, Message } from "../chat/chat_port";

function page(messages: Message[]): ConversationMessagesResponse {
  return {
    conversation_id: "1",
    messages,
    user_interaction_state: {
      text_input_state: "ENABLED",
      text_input_placeholder: "Ask about a chain",
      thinking_state: null,
    },
    turn: null,
  };
}
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
      stop_turn: async ({ turn_id }) => ({
        turn_id,
        conversation_id: "1",
        status: "cancelled",
        from_message: "m_user",
      }),
      post_message: async () => ({
        turn: {
          turn_id: "t_1",
          conversation_id: "1",
          status: "queued",
          from_message: "m_user",
        },
        received_message: {
          kind: "markdown",
          message_id: "m_user",
          role: "user",
          text: "hello",
          created_timestamp: "2026-09-30T00:00:00+00:00",
        },
      }),
      list_messages: async () => ({ messages: [], next_cursor: null }),
      subscribe_turn: async function* (): AsyncGenerator<ConversationMessagesResponse> {
        yield page([
          {
            kind: "markdown",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_a",
            role: "agent",
            text: "creating a case",
          },
        ]);
        yield page([{ kind: "heartbeat", message_id: "m_h", role: "meta" }]);
        yield page([
          {
            kind: "deeplink",
            created_timestamp: "2026-09-30T00:00:00+00:00",
            message_id: "m_d",
            role: "other",
            link: `causal_chains://chain?root_situation_id=${now_id}&root_version=1&title=now`,
          },
        ]);
      },
    };
    const chain_port: ChainPort = {
      get_chains: async () => [
        {
          situations: [
            {
              situation_id: now_id,
              version: 1,
              title: "Strait shut",
              desc: "strait shut",
              potential_drivers: ["blockade"],
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
    expect(host.textContent).not.toContain("working through the chain");
    expect(host.querySelector(".heartbeat")).toBeNull();
    expect(host.querySelector(".chain-canvas")).toBeNull();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 80));
    });
    expect(host.textContent).not.toContain("working through the chain");
    expect(host.querySelector(".heartbeat")).toBeNull();
    expect(host.textContent).toContain("causal_chains://chain");
    expect(host.querySelector(".chain-canvas")).not.toBeNull();
    expect(host.querySelector(".node-title")?.textContent).toBe("Strait shut");
    expect(host.textContent).toContain("strait shut");
    act(() => {
      root.unmount();
    });
    host.remove();
  });
});
