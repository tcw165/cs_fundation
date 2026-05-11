/**
 * Relative file paths that differ between two trees. Prune recursion where `hash` matches.
 * Only **files** should appear (not directory-only paths unless you document otherwise).
 *
 * @param before - Root path of the “before” snapshot (e.g. `./before`).
 * @param after - Root path of the “after” snapshot (e.g. `./after`).
 */
export function diff(before: string, after: string): string[] {
  void before;
  void after;
  throw new Error("diff: not implemented");
}
