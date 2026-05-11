import assert from "node:assert";
import { describe, it } from "node:test";
import {
  buildMerkleTree,
  defaultSha256MerkleOperator,
  diff,
} from "./merkle.js";

describe("defaultSha256MerkleOperator (computing operator)", () => {
  const op = defaultSha256MerkleOperator;

  it("hashFile is SHA-256 hex of bytes", () => {
    assert.strictEqual(
      op.hashFile(Buffer.from("hello", "utf8")),
      "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
    );
  });

  it("combineChildHashes returns the sole digest for one child", () => {
    const h = op.hashFile(Buffer.from("only", "utf8"));
    assert.strictEqual(op.combineChildHashes([h]), h);
  });

  it("combineChildHashes pairs two digests", () => {
    const a = op.hashFile(Buffer.from("a", "utf8"));
    const b = op.hashFile(Buffer.from("b", "utf8"));
    const root = op.combineChildHashes([a, b]);
    assert.notStrictEqual(root, a);
    assert.strictEqual(root, op.combineChildHashes([a, b]));
  });

  it("combineChildHashes duplicates last when count is odd", () => {
    const a = op.hashFile(Buffer.from("a", "utf8"));
    const b = op.hashFile(Buffer.from("b", "utf8"));
    const c = op.hashFile(Buffer.from("c", "utf8"));
    const r1 = op.combineChildHashes([a, b, c]);
    const r2 = op.combineChildHashes([a, b, c, c]);
    assert.strictEqual(r1, r2);
  });

  it("combineChildHashes defines empty directory digest", () => {
    const empty = op.combineChildHashes([]);
    assert.strictEqual(typeof empty, "string");
    assert.strictEqual(empty.length, 64);
  });
});

describe("buildMerkleTree", () => {
  it.skip("walks a directory and fills hashes via MerkleOperator", () => {
    void buildMerkleTree;
    assert.fail("enable when implemented");
  });
});

describe("diff", () => {
  it.skip("returns changed file paths and prunes matching subtrees", () => {
    void diff;
    assert.fail("enable when implemented");
  });
});
