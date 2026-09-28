import {
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";

import { DeeplinkCardPart } from "../chain/deeplink_card";

import "./thread.css";

function UserMessage() {
  return (
    <MessagePrimitive.Root className="message message-user">
      <MessagePrimitive.Parts />
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="message message-assistant">
      <MessagePrimitive.Parts
        components={{
          data: {
            by_name: {
              deeplink_widget: DeeplinkCardPart,
            },
          },
        }}
      />
    </MessagePrimitive.Root>
  );
}

export function Thread() {
  return (
    <ThreadPrimitive.Root className="thread">
      <ThreadPrimitive.Viewport className="thread-viewport">
        <ThreadPrimitive.Empty>
          Ask about a causal chain.
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            AssistantMessage,
          }}
        />
      </ThreadPrimitive.Viewport>
      <ComposerPrimitive.Root className="composer">
        <ComposerPrimitive.Input
          className="composer-input"
          placeholder="Message"
        />
        <ComposerPrimitive.Send className="composer-send">Send</ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}
