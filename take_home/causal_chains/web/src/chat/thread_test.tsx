// @vitest-environment jsdom

import type { ReactElement } from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it } from "vitest";

import type { ChatPort, ConversationMessagesResponse, UserInteractionState } from "./chat_port";
import { fast_timing } from "./reveal_timing";
import { Thread } from "./thread";
import { use_chat_session } from "./use_chat_session";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

function render(node: ReactElement) {
  const host = document.createElement("div");
  document.body.append(host);
  const root = createRoot(host);
  act(() => {
    root.render(node);
  });
  return { host, root };
}

function interaction(
  text_input_state: UserInteractionState["text_input_state"],
  thinking: string | null,
): UserInteractionState {
  return {
    text_input_state,
    text_input_placeholder: "Ask about a chain",
    thinking_state: thinking === null ? null : { text: thinking },
  };
}

function page(state: UserInteractionState): ConversationMessagesResponse {
  return {
    conversation_id: "1",
    messages: [
      {
        kind: "markdown",
        message_id: "m_a",
        role: "agent",
        text: "one",
        created_timestamp: "2026-09-30T00:00:00+00:00",
      },
    ],
    user_interaction_state: state,
    turn: { processing: [], queued: [] },
  };
}

function Harness({ chat_port }: { chat_port: ChatPort }) {
  const session = use_chat_session(chat_port, "1", fast_timing);
  return <Thread session={session} on_open_link={() => undefined} />;
}

async function send(host: HTMLElement, text: string) {
  const input = host.querySelector("textarea");
  await act(async () => {
    if (input instanceof HTMLTextAreaElement) {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype,
        "value",
      )?.set;
      setter?.call(input, text);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  await act(async () => {
    host.querySelector("form")?.dispatchEvent(
      new Event("submit", { bubbles: true, cancelable: true }),
    );
    await Promise.resolve();
  });
}

describe("thread composer", () => {
  it("shows Stop and thinking text from the snapshot", async () => {
    const chat_port: ChatPort = {
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
      subscribe_turn: async function* () {
        yield page(interaction("SEND_ENABLED_WITH_STOP_BUTTON", "Looking up the chain"));
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    const before = host.querySelector("textarea");
    expect(before?.getAttribute("placeholder")).toContain("NVDA");
    expect(host.querySelector("[aria-label='Stop']")).toBeNull();
    await send(host, "hello");
    expect(host.querySelector("[aria-label='Stop']")).not.toBeNull();
    expect(host.textContent).toContain("Looking up the chain");
    expect(host.querySelector("textarea")?.getAttribute("placeholder")).toBe(
      "Ask about a chain",
    );
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("removes the field when the snapshot hides it", async () => {
    const chat_port: ChatPort = {
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
      subscribe_turn: async function* () {
        yield page(interaction("HIDDEN", null));
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    await send(host, "hello");
    expect(host.querySelector("textarea")).toBeNull();
    act(() => {
      root.unmount();
    });
    host.remove();
  });
});
