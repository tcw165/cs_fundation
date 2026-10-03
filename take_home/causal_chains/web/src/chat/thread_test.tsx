// @vitest-environment jsdom

import type { ReactElement } from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it } from "vitest";

import type {
  ChatPort,
  ConversationMessagesResponse,
  Message,
  UserInteractionState,
} from "./chat_port";
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
      subscribe_turn: async function* () {
        yield page(interaction("SEND_ENABLED_WITH_STOP_BUTTON", "Looking up the chain"));
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    const before = host.querySelector("textarea");
    expect(before?.getAttribute("placeholder")).toContain("NVDA");
    expect(host.querySelector("[aria-label='Stop']")).toBeNull();
    expect(host.querySelector("[aria-label='Send']")).not.toBeNull();
    await send(host, "hello");
    const stop = host.querySelector("[aria-label='Stop']");
    expect(stop).not.toBeNull();
    expect(stop?.classList.contains("composer-send")).toBe(true);
    expect(stop?.querySelector("rect")).not.toBeNull();
    expect(host.querySelector("[aria-label='Send']")).toBeNull();
    expect(host.textContent).toContain("Looking up the chain");
    expect(host.querySelector("textarea")?.getAttribute("placeholder")).toBe(
      "Ask about a chain",
    );
    const square = stop?.querySelector("rect");
    expect(square?.getAttribute("width")).toBe("12");
    expect(square?.getAttribute("height")).toBe("12");
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("posts stop for the turn when Stop is clicked", async () => {
    const stopped: string[] = [];
    const chat_port: ChatPort = {
      stop_turn: async ({ turn_id }) => {
        stopped.push(turn_id);
        return {
          turn_id,
          conversation_id: "1",
          status: "cancelled",
          from_message: "m_user",
        };
      },
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
      subscribe_turn: async function* () {
        yield page(interaction("SEND_ENABLED_WITH_STOP_BUTTON", null));
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    await send(host, "hello");
    const stop = host.querySelector("[aria-label='Stop']");
    await act(async () => {
      stop?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await Promise.resolve();
    });
    expect(stopped).toEqual(["t_1"]);
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("removes the field when the snapshot hides it", async () => {
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

  it("shows a message id once when the stream repeats it", async () => {
    const snapshot = page(interaction("ENABLED", null));
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
      subscribe_turn: async function* () {
        yield snapshot;
        yield snapshot;
        yield {
          ...snapshot,
          messages: [
            {
              kind: "markdown",
              message_id: "m_user",
              role: "user",
              text: "hello",
              created_timestamp: "2026-09-30T00:00:00+00:00",
            },
          ],
        };
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    await send(host, "hello");
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 80));
    });
    expect(host.querySelectorAll(".message-assistant")).toHaveLength(1);
    expect(host.querySelectorAll(".message-user")).toHaveLength(1);
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("shows stored messages when the chat opens", async () => {
    const earlier: Message = {
      kind: "markdown",
      message_id: "m_user",
      role: "user",
      text: "earlier",
      created_timestamp: "2026-09-30T00:00:00+00:00",
    };
    const saved: Message = {
      kind: "markdown",
      message_id: "m_a",
      role: "agent",
      text: "saved",
      created_timestamp: "2026-09-30T00:00:01+00:00",
    };
    const later: Message = {
      kind: "markdown",
      message_id: "m_b",
      role: "agent",
      text: "later",
      created_timestamp: "2026-09-30T00:00:02+00:00",
    };
    const pages = [
      { messages: [earlier, saved], next_cursor: "MSG#1" },
      { messages: [saved, later], next_cursor: null },
    ];
    let index = 0;
    const chat_port: ChatPort = {
      stop_turn: async ({ turn_id }) => ({
        turn_id,
        conversation_id: "1",
        status: "cancelled",
        from_message: "m_user",
      }),
      post_message: async () => {
        throw new Error("unused");
      },
      list_messages: async () => pages[index++] ?? { messages: [], next_cursor: null },
      subscribe_turn: async function* () {},
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(host.querySelectorAll(".message-user")).toHaveLength(1);
    expect(host.textContent).toContain("earlier");
    expect(host.textContent).toContain("saved");
    expect(host.textContent).toContain("later");
    expect(host.querySelectorAll(".message-assistant")).toHaveLength(2);
    expect(host.querySelectorAll("time")).toHaveLength(1);
    expect(host.querySelector("time")?.getAttribute("datetime")).toBe(
      "2026-09-30T00:00:02+00:00",
    );
    expect(host.querySelector(".message-separator")).toBeNull();
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("separates a message that is more than five minutes later", async () => {
    const first: Message = {
      kind: "markdown",
      message_id: "m_user",
      role: "user",
      text: "earlier",
      created_timestamp: "2026-10-01T07:00:00.000Z",
    };
    const second: Message = {
      kind: "markdown",
      message_id: "m_a",
      role: "agent",
      text: "saved",
      created_timestamp: "2026-10-01T07:06:00.000Z",
    };
    const chat_port: ChatPort = {
      stop_turn: async ({ turn_id }) => ({
        turn_id,
        conversation_id: "1",
        status: "cancelled",
        from_message: "m_user",
      }),
      post_message: async () => {
        throw new Error("unused");
      },
      list_messages: async () => ({ messages: [first, second], next_cursor: null }),
      subscribe_turn: async function* () {},
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(host.querySelectorAll(".message-separator")).toHaveLength(1);
    expect(host.querySelector(".message-separator time")?.getAttribute("datetime")).toBe(
      "2026-10-01T07:00:00.000Z",
    );
    expect(host.querySelector(".message-user time")?.getAttribute("datetime")).toBe(
      "2026-10-01T07:00:00.000Z",
    );
    expect(host.querySelector(".message-assistant time")?.getAttribute("datetime")).toBe(
      "2026-10-01T07:06:00.000Z",
    );
    expect(host.querySelectorAll("time")).toHaveLength(3);
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("pins the viewport to the bottom while the turn stream is open", async () => {
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
      subscribe_turn: async function* () {
        yield page(interaction("SEND_ENABLED_WITH_STOP_BUTTON", "Looking up the chain"));
        await new Promise(() => undefined);
      },
    };
    const { host, root } = render(<Harness chat_port={chat_port} />);
    const viewport = host.querySelector(".thread-viewport");
    if (!(viewport instanceof HTMLDivElement)) {
      throw new Error("missing viewport");
    }
    Object.defineProperty(viewport, "scrollHeight", { configurable: true, get: () => 900 });
    Object.defineProperty(viewport, "clientHeight", { configurable: true, get: () => 200 });
    viewport.scrollTop = 10;
    await send(host, "hello");
    expect(viewport.scrollTop).toBe(900);
    act(() => {
      root.unmount();
    });
    host.remove();
  });
});
