# Quiz: ts-streaming-parser

Implement a small streaming parser for newline-delimited JSON (NDJSON): text arrives in arbitrary chunk boundaries; you must buffer incomplete lines and emit complete JSON values (parse each full line with `JSON.parse`).

## API

Suggested shape (align your implementation with [`parser.ts`](./parser.ts)):

```ts
createNdjsonParser() -> {
  push(chunk: string): unknown[];
  flush(): unknown[];
}
```

- **`push`** — Append data; return every fully parsed line-delimited JSON value (in order).
- **`flush`** — Parse any remaining buffered full line (ignore a trailing partial line without newline).
- Empty lines are ignored.

## Tests

[`parser_test.ts`](./parser_test.ts) is the contract. Run:

```bash
bazel test //quiz/ts-streaming-parser:ndjson_test
```
