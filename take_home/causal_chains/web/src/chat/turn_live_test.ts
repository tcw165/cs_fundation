import { describe, expect, it } from "vitest";

import type { Turn, TurnDescriptor } from "./chat_port";
import { turn_is_live } from "./turn_live";

function turn(status: string): Turn {
  return {
    turn_id: "t_1",
    conversation_id: "1",
    status,
    from_message: "m_user",
  };
}

function descriptor(processing: Turn[] = [], queued: Turn[] = []): TurnDescriptor {
  return { processing, queued };
}

describe("turn_is_live", () => {
  it("is live when a turn is processing", () => {
    expect(turn_is_live(descriptor([turn("running")]))).toBe(true);
    expect(turn_is_live(descriptor([turn("queued")]))).toBe(true);
  });

  it("is hidden when processing is empty", () => {
    expect(turn_is_live(null)).toBe(false);
    expect(turn_is_live(undefined)).toBe(false);
    expect(turn_is_live(descriptor())).toBe(false);
    expect(turn_is_live(descriptor([], [turn("queued")]))).toBe(false);
  });
});
