import assert from "node:assert";
import fs from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import { diff } from "./merkle.js";

type SnapshotSpec = Record<string, string>;

async function resetDir(absPath: string): Promise<void> {
  await fs.rm(absPath, { recursive: true, force: true });
  await fs.mkdir(absPath, { recursive: true });
}

async function writeSnapshot(rootDir: string, spec: SnapshotSpec): Promise<void> {
  for (const [relPath, contents] of Object.entries(spec)) {
    const absFile = path.join(rootDir, relPath);
    await fs.mkdir(path.dirname(absFile), { recursive: true });
    await fs.writeFile(absFile, contents, "utf8");
  }
}

async function makeFixtureAt(
  fixtureRoot: string,
  before: SnapshotSpec,
  after: SnapshotSpec,
): Promise<{ beforeDir: string; afterDir: string }> {
  const beforeDir = path.join(fixtureRoot, "before");
  const afterDir = path.join(fixtureRoot, "after");

  await resetDir(beforeDir);
  await resetDir(afterDir);
  await writeSnapshot(beforeDir, before);
  await writeSnapshot(afterDir, after);

  return { beforeDir, afterDir };
}

describe("fixtures", () => {
  it("test case 1: /tmp/merkle_test_1 depth-1 rename only", async () => {
    const { beforeDir, afterDir } = await makeFixtureAt(
      "/tmp/merkle_test_1",
      { "old.txt": "same-contents" },
      { "new.txt": "same-contents" },
    );

    // Smoke check: expected files exist.
    await assert.doesNotReject(async () => fs.stat(path.join(beforeDir, "old.txt")));
    await assert.doesNotReject(async () => fs.stat(path.join(afterDir, "new.txt")));
  });

  it("test case 2: /tmp/merkle_test_2 depth-3 one file content change", async () => {
    const { beforeDir, afterDir } = await makeFixtureAt(
      "/tmp/merkle_test_2",
      {
        "a.txt": "unchanged",
        "d1/d2/d3/target.txt": "before",
      },
      {
        "a.txt": "unchanged",
        "d1/d2/d3/target.txt": "after",
      },
    );

    await assert.doesNotReject(async () => fs.stat(path.join(beforeDir, "d1/d2/d3/target.txt")));
    await assert.doesNotReject(async () => fs.stat(path.join(afterDir, "d1/d2/d3/target.txt")));
  });

  it("extra: add + delete (useful for diff)", async () => {
    await makeFixtureAt(
      "/tmp/merkle_test_add_delete",
      { "keep.txt": "k", "gone.txt": "bye" },
      { "keep.txt": "k", "added.txt": "hi" },
    );
  });

  it("extra: nested rename + modify (useful for diff)", async () => {
    await makeFixtureAt(
      "/tmp/merkle_test_nested_rename_modify",
      { "src/a.txt": "same", "src/b.txt": "old" },
      { "src/a_renamed.txt": "same", "src/b.txt": "new" },
    );
  });
});

describe("diff", () => {
  it("throws until implemented", () => {
    assert.throws(() => diff("./before", "./after"), /diff: not implemented/);
  });

  it.skip("returns changed file paths and prunes matching subtrees", () => {
    void diff;
    assert.fail("enable when implemented");
  });
});
