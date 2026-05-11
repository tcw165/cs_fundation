import { createHash } from "node:crypto";

/**
 * Generic Merkle tree node: directories have `children`, file leaves have `content`.
 * `hash` must be derivable from `content` (leaves) or from child hashes (internal) via
 * {@link MerkleOperator}.
 */
export type MerkleTree<TMeta = unknown> = {
  hash: string;
  /** Path relative to snapshot root (POSIX); `""` for root. */
  relPath: string;
  children?: MerkleTree<TMeta>[];
  content?: Buffer;
  /** Optional metadata (modes, symlinks policy, etc.). */
  meta?: TMeta;
};

/**
 * Computing operator: how file bytes and ordered child digests become node hashes.
 * Implementations should document ordering (e.g. lexicographic by `relPath`).
 */
export interface MerkleOperator {
  /** Digest for a file leaf from raw bytes. */
  hashFile(content: Buffer): string;
  /**
   * Digest for a directory from **sorted** child node digests (lowercase hex, 64 chars each).
   * Empty directory: define a deterministic rule (e.g. hash of empty buffer).
   */
  combineChildHashes(childHashesSorted: readonly string[]): string;
}

function combineDigestPair(leftHex: string, rightHex: string): string {
  const left = Buffer.from(leftHex, "hex");
  const right = Buffer.from(rightHex, "hex");
  return createHash("sha256").update(Buffer.concat([left, right])).digest("hex");
}

/** Binary reduction: duplicate last when odd width, pair left-to-right. */
function reduceBinaryMerkle(digests: readonly string[]): string {
  if (digests.length === 0) {
    return createHash("sha256").update(Buffer.alloc(0)).digest("hex");
  }
  let level = [...digests];
  while (level.length > 1) {
    if (level.length % 2 === 1) {
      level = [...level, level[level.length - 1]!];
    }
    const next: string[] = [];
    for (let i = 0; i < level.length; i += 2) {
      next.push(combineDigestPair(level[i]!, level[i + 1]!));
    }
    level = next;
  }
  return level[0]!;
}

/** Default SHA-256 operator (hex digests). */
export const defaultSha256MerkleOperator: MerkleOperator = {
  hashFile(content: Buffer): string {
    return createHash("sha256").update(content).digest("hex");
  },
  combineChildHashes(childHashesSorted: readonly string[]): string {
    return reduceBinaryMerkle(childHashesSorted);
  },
};

/**
 * Walk `rootDir` and build a Merkle tree over file contents; internal node per subdirectory.
 * Use `operator` for all hashes (default: {@link defaultSha256MerkleOperator}).
 */
export function buildMerkleTree(
  rootDir: string,
  operator: MerkleOperator = defaultSha256MerkleOperator,
): MerkleTree {
  void rootDir;
  void operator;
  throw new Error("buildMerkleTree: not implemented");
}

/**
 * Relative file paths that differ between two trees. Prune recursion where `hash` matches.
 * Only **files** should appear (not directory-only paths unless you document otherwise).
 */
export function diff(treeA: MerkleTree, treeB: MerkleTree): string[] {
  void treeA;
  void treeB;
  throw new Error("diff: not implemented");
}
