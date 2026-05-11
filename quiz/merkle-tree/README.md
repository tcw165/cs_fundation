# Quiz: Merkle sync engine

**Round 2 — Technical phone screen (60 min, coding)**

## Scenario

You are given a repo skeleton with two directory snapshots, `./before` and `./after`, representing a user’s codebase at two points in time. Model each snapshot as a tree: files are leaves (content-addressed), directories are internal nodes whose hash summarizes their children.

Implement a **Merkle sync engine**: build trees from disk (or from an in-memory representation mirroring those folders), compare two trees efficiently, and optionally serialize trees for a minimal wire protocol.

---

## Requirements

### 1. `buildMerkleTree(dir)`

Walk `dir` (e.g. `./before` or `./after`) and produce a **Merkle tree** over the filesystem:

- **Leaves** correspond to **files**; hash file **contents** (not metadata like mtime unless you explicitly define and document it).
- **Internal nodes** correspond to **subdirectories** (and the root): each directory’s digest must deterministically combine its children so identical subtrees yield identical hashes.

Decisions you should make explicit (in comments or a short note):

- Sorting of children (e.g. lexicographic by relative path) so ordering is stable.
- Empty directories and empty files.
- Symlinks, binary vs text — pick a reasonable rule and state it.

### 2. `diff(treeA, treeB)`

Return the **list of file paths** (relative to the snapshot root) that **changed** between the two trees.

- **Changed** includes: added, removed, or content-modified files.
- Efficiency matters: **do not** compare every path blindly if you can avoid it — walk **only subtrees whose Merkle hashes differ** (prune where `hash(subtreeA) === hash(subtreeB)`).

Output format: e.g. sorted relative POSIX paths, or `{ path, kind: 'added' | 'removed' | 'modified' }[]` — stay consistent and document your choice.

### 3. Bonus (if time)

**Serialize** the tree compactly so a “server” could persist it and a “client” could transmit **only what’s needed** for the other side to validate or reconstruct a diff (e.g. root hash + selective proofs, or a canonical serialized trie). Sketch the format and how it would pair with `diff`.

---

## Foundational hashing (building blocks)

For **ordered lists of leaf digests**, the scaffold in this package uses SHA-256 and a fixed pairing rule so tests stay deterministic:

| Piece | Rule |
| --- | --- |
| Digest encoding | Lowercase hex (`digest('hex')`). |
| Combining two child digests | Decode each hex string to 32 bytes, concatenate **left ‖ right**, SHA-256 the 64-byte buffer. |
| Odd-width level | Duplicate the **last** hash once before pairing. |

See [`merkle.ts`](./merkle.ts): generic `MerkleTree`, `MerkleOperator`, and `defaultSha256MerkleOperator` (SHA-256 file hash + binary pairing over sorted child digests). Implement `buildMerkleTree` and `diff`; extend the tree type with `meta` if you need extra fields.

---

## Tests in this repo

[`merkle_test.ts`](./merkle_test.ts) exercises **`defaultSha256MerkleOperator`**. Skipped cases document **`buildMerkleTree`** and **`diff`** — un-skip and assert when you implement them.

```bash
bazel test //quiz/merkle-tree:merkle_test
```

---

## API layout (fill in)

All public types and stubs live in [`merkle.ts`](./merkle.ts). Replace the `throw new Error(...)` bodies in `buildMerkleTree` and `diff` with your implementation.
