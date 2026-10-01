import { describe, expect, it } from "vitest";

import { overlay_thumb_box } from "./overlay_scroll";

describe("overlay_thumb_box", () => {
  it("stays hidden when the pane does not overflow", () => {
    expect(overlay_thumb_box(0, 400, 400, 0, 400)).toBeNull();
  });

  it("rides the open track and ends flush with it", () => {
    const start = overlay_thumb_box(0, 800, 400, 28, 200);
    const end = overlay_thumb_box(400, 800, 400, 28, 200);
    expect(start).toEqual({ top: 28, height: 100 });
    expect((end?.top ?? 0) + (end?.height ?? 0)).toBe(228);
  });
});
