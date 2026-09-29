import { describe, expect, it } from "vitest";

import { panel_from_link } from "./panel_state";

describe("panel_from_link", () => {
  it("unfolds the panel and keeps a chain focus", () => {
    expect(
      panel_from_link("causal_chains://chain?root_situation_id=now&root_version=1&title=Hormuz"),
    ).toEqual({
      open: true,
      focus: {
        kind: "chain",
        root_situation_id: "now",
        root_version: 1,
        title: "Hormuz",
      },
    });
  });

  it("unfolds the panel for a stored case", () => {
    expect(
      panel_from_link("causal_chains://chain/22222222-2222-4222-8222-222222222222"),
    ).toEqual({
      open: true,
      focus: {
        kind: "case",
        case_id: "22222222-2222-4222-8222-222222222222",
        title: "",
      },
    });
  });

  it("centers an edge when the link names one", () => {
    expect(
      panel_from_link(
        "causal_chains://edge?from_situation_id=a&from_version=1&to_situation_id=b&to_version=1",
      )?.focus,
    ).toEqual({
      kind: "edge",
      from_situation_id: "a",
      from_version: 1,
      to_situation_id: "b",
      to_version: 1,
    });
  });
});
