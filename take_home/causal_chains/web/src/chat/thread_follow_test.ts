import { describe, expect, it } from "vitest";

import { distance_from_bottom, still_following } from "./thread_follow";

describe("thread follow", () => {
  it("treats the bottom of the viewport as followed", () => {
    expect(distance_from_bottom(400, 800, 400)).toBe(0);
    expect(still_following(0)).toBe(true);
    expect(still_following(48)).toBe(true);
  });

  it("lets go once the reader has moved up the log", () => {
    expect(distance_from_bottom(100, 800, 400)).toBe(300);
    expect(still_following(300)).toBe(false);
  });
});
