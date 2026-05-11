# Quiz: Merkle sync engine

**Round 2 — Technical phone screen (60 min, coding)**

## Scenario

You are given two directory snapshots (e.g. `./before` and `./after`) representing a user’s codebase at two points in time. Build a **Merkle tree** over file contents with an internal node per subdirectory, then report which **files** changed.

---

## Requirements

Implement **`diff(before, after)`** in [`merkle.ts`](./merkle.ts):

- **`before`**, **`after`** — Absolute or relative paths to the roots of each snapshot.
- **Return** — Relative file paths (from each snapshot root) that **changed**: added, removed, or content-modified.
- **Efficiency** — Walk **only** subtrees whose Merkle hashes differ; do not rescan identical subtrees.

Document your choices: child ordering, empty files/directories, symlinks, binary vs text.

### Bonus (if time)

Serialize the tree compactly for a server/client so the client can send a minimal diff payload.

---

## Tests

[`merkle_test.ts`](./merkle_test.ts) includes a placeholder skipped test for the real contract once you implement `diff`.

```bash
bazel test //quiz/merkle-tree:merkle_test
```

---

## API

Public surface is only:

```ts
export function diff(before: string, after: string): string[];
```

Implement Merkle hashing and tree walks inside this module (private helpers) as you prefer.
