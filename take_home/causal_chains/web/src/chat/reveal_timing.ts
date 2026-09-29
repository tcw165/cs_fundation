export type RevealTiming = {
  markdown_ms: (text: string) => number;
  deeplink_ms: number;
  heartbeat_ms: number;
};

export const studio_timing: RevealTiming = {
  markdown_ms: (text) => Math.min(900, 280 + text.length * 6),
  deeplink_ms: 480,
  heartbeat_ms: 200,
};

export const fast_timing: RevealTiming = {
  markdown_ms: () => 24,
  deeplink_ms: 24,
  heartbeat_ms: 12,
};

export function item_duration_ms(
  item: { type: string; text?: string },
  timing: RevealTiming,
): number {
  if (item.type === "markdown") {
    return timing.markdown_ms(item.text ?? "");
  }
  if (item.type === "deeplink") {
    return timing.deeplink_ms;
  }
  return timing.heartbeat_ms;
}
