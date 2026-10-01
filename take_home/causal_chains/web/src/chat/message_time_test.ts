import { describe, expect, it } from "vitest";

import { message_marks } from "./message_time";

const start = Date.parse("2026-10-01T07:00:00.000Z");

function at(offset_ms: number): string {
  return new Date(start + offset_ms).toISOString();
}

describe("message_marks", () => {
  it("shows a timestamp only on the last message of a one-minute cluster", () => {
    const marks = message_marks([at(0), at(30_000), at(59_000)]);
    expect(marks.map((mark) => mark.show_timestamp)).toEqual([false, false, true]);
    expect(marks.every((mark) => mark.show_separator === false)).toBe(true);
  });

  it("shows both timestamps when the next message is more than a minute away", () => {
    const marks = message_marks([at(0), at(61_000)]);
    expect(marks.map((mark) => mark.show_timestamp)).toEqual([true, true]);
    expect(marks.map((mark) => mark.show_separator)).toEqual([false, false]);
  });

  it("separates a message more than five minutes from the previous one", () => {
    const exact = message_marks([at(0), at(5 * 60_000)]);
    expect(exact.map((mark) => mark.show_separator)).toEqual([false, false]);
    const later = message_marks([at(0), at(5 * 60_000 + 1)]);
    expect(later.map((mark) => mark.show_separator)).toEqual([false, true]);
    const older = message_marks([at(6 * 60_000), at(0)]);
    expect(older.map((mark) => mark.show_separator)).toEqual([false, true]);
  });

  it("ignores a heartbeat when measuring the gap", () => {
    const marks = message_marks([at(0), null, at(10_000)]);
    expect(marks).toEqual([
      { show_timestamp: false, show_separator: false },
      { show_timestamp: false, show_separator: false },
      { show_timestamp: true, show_separator: false },
    ]);
  });
});
