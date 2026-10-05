import { describe, expect, it } from "vitest";

import {
  fork_comment,
  join_comment,
  prepend_fork_comment,
  split_leading_comment,
} from "./composer_comment";

const situation_id = "e5e7887d-e05d-4743-91f2-8930e106731c";

describe("composer comment", () => {
  it("spells a fork as a leading comment block", () => {
    const text = prepend_fork_comment("keep this", situation_id);
    expect(text).toBe(
      `<comment>\nFork the causal chain from situation ID: ${situation_id}\n<comment/>\nkeep this`,
    );
    expect(split_leading_comment(text)).toEqual({
      comment: fork_comment(situation_id),
      rest: "keep this",
    });
  });

  it("replaces an existing fork comment and keeps the typed rest", () => {
    const first = prepend_fork_comment("after", situation_id);
    const next = prepend_fork_comment(first, "22222222-2222-4222-8222-222222222222");
    expect(split_leading_comment(next)).toEqual({
      comment: fork_comment("22222222-2222-4222-8222-222222222222"),
      rest: "after",
    });
  });

  it("leaves ordinary text untouched", () => {
    expect(split_leading_comment("hello")).toEqual({ comment: null, rest: "hello" });
    expect(join_comment(null, "hello")).toBe("hello");
  });
});
