import assert from "node:assert";
import { describe, it } from "node:test";
import { diff } from "./merkle.js";

describe("diff", () => {
  it("throws until implemented", () => {
    assert.throws(() => diff("./before", "./after"), /diff: not implemented/);
  });

  it.skip("returns changed file paths and prunes matching subtrees", () => {
    void diff;
    assert.fail("enable when implemented");
  });
});
