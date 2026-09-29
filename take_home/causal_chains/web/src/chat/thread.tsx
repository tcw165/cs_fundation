import {
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAuiState,
} from "@assistant-ui/react";

import { DeeplinkCardPart } from "../chain/deeplink_card";
import { MicIcon, SendIcon } from "../shell/icons";
import { Suggestions } from "./suggestions";

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
  const empty = useAuiState((state) => state.thread.messages.length === 0);
  return (
    <ThreadPrimitive.Root className="thread">
      <ThreadPrimitive.Viewport className="thread-viewport">
        {empty ? <h2 className="play-title">What's the play?</h2> : null}
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
          placeholder="Short $NVDA if chance of China-Taiwan war goes to over 90%"
          rows={1}
          aria-label="Message"
        />
        <div className="composer-tools">
          <span className="composer-mic" aria-hidden="true">
            <MicIcon />
          </span>
          <ComposerPrimitive.Send className="composer-send" aria-label="Send">
            <SendIcon />
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
      {empty ? <Suggestions /> : null}
    </ThreadPrimitive.Root>
  );
}
