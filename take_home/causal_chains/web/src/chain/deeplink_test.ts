import { describe, expect, it } from "vitest";

import { deeplink_href, parse_deeplink } from "./deeplink";

describe("parse_deeplink", () => {
  it("reads causal_chains://chain, situation, and edge routes", () => {
    expect(
      parse_deeplink(
        "causal_chains://chain?root_situation_id=now&root_version=1&title=Hormuz",
      ),
    ).toEqual({
      route: "chain",
      root_situation_id: "now",
      root_version: 1,
      title: "Hormuz",
    });
    expect(
      parse_deeplink("causal_chains://situation?situation_id=step&version=2"),
    ).toEqual({
      route: "situation",
      situation_id: "step",
      version: 2,
    });
    expect(
      parse_deeplink(
        "causal_chains://edge?from_situation_id=a&from_version=1&to_situation_id=b&to_version=1",
      ),
    ).toEqual({
      route: "edge",
      from_situation_id: "a",
      from_version: 1,
      to_situation_id: "b",
      to_version: 1,
    });
  });

  it("still accepts the legacy /chain path", () => {
    expect(parse_deeplink("/chain/now/1?title=Hormuz")).toEqual({
      route: "chain",
      root_situation_id: "now",
      root_version: 1,
      title: "Hormuz",
    });
  });

  it("reads a stored chain as causal_chains://chain/<case_id>", () => {
    const case_id = "22222222-2222-4222-8222-222222222222";
    const link = { route: "case" as const, case_id };
    expect(parse_deeplink(`causal_chains://chain/${case_id}`)).toEqual(link);
    expect(parse_deeplink(deeplink_href(link))).toEqual(link);
  });

  it("round-trips a chain link", () => {
    const link = {
      route: "chain" as const,
      root_situation_id: "now",
      root_version: 1,
      title: "Hormuz open",
    };
    expect(parse_deeplink(deeplink_href(link))).toEqual(link);
  });
});
