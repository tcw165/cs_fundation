export interface NdjsonParser {
  /** Append text and return each full NDJSON value parsed from completed lines. */
  push(chunk: string): unknown[];
  /**
   * Drain complete lines still buffered (same as pushing an empty chunk).
   * A trailing segment with no `\n` remains buffered (incomplete line).
   */
  flush(): unknown[];
}

/** Newline-delimited JSON: buffer chunks, emit parsed JSON for each complete line. */
export function createNdjsonParser(): NdjsonParser {
  let buffer = "";

  const parseLine = (line: string): unknown | undefined => {
    const trimmed = line.trim();
    if (trimmed.length === 0) {
      return undefined;
    }
    return JSON.parse(trimmed) as unknown;
  };

  const push = (chunk: string): unknown[] => {
    buffer += chunk;
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    const out: unknown[] = [];
    for (const line of lines) {
      const value = parseLine(line);
      if (value !== undefined) {
        out.push(value);
      }
    }
    return out;
  };

  const flush = (): unknown[] => push("");

  return { push, flush };
}
