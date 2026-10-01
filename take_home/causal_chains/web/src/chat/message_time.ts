export const TIMESTAMP_CLUSTER_MS = 60_000;
export const SEPARATOR_GAP_MS = 5 * 60_000;

export type MessageMark = {
  show_timestamp: boolean;
  show_separator: boolean;
};

export function message_marks(timestamps: Array<string | null>): MessageMark[] {
  const marks = timestamps.map(() => ({
    show_timestamp: false,
    show_separator: false,
  }));
  const timed = timestamps.flatMap((timestamp, index) =>
    timestamp === null ? [] : [{ timestamp, index, ms: Date.parse(timestamp) }],
  );
  for (let position = 0; position < timed.length; position += 1) {
    const current = timed[position];
    if (current === undefined) {
      continue;
    }
    const previous = timed[position - 1];
    const next = timed[position + 1];
    if (previous !== undefined && Math.abs(current.ms - previous.ms) > SEPARATOR_GAP_MS) {
      marks[current.index] = { ...marks[current.index], show_separator: true };
    }
    const next_gap = next === undefined ? Infinity : Math.abs(next.ms - current.ms);
    marks[current.index] = {
      ...marks[current.index],
      show_timestamp: next_gap > TIMESTAMP_CLUSTER_MS,
    };
  }
  return marks;
}

export function format_message_time(created_timestamp: string): string {
  return new Date(created_timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}
