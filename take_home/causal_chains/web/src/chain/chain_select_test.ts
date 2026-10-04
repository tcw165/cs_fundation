import { describe, expect, it } from "vitest";

import type { CausalChain, DeeplinkCard } from "./chain_port";
import { chain_for_card, chain_for_focus } from "./chain_select";

const now_id = "11111111-1111-4111-8111-111111111111";
const other_id = "33333333-3333-4333-8333-333333333333";

function chain(root_id: string, desc: string): CausalChain {
  return {
    situations: [
      {
        situation_id: root_id,
        version: 1,
        created_timestamp: "2026-10-01T00:00:00+00:00",
        kind: "start",
        title: desc,
        desc,
        remained_drivers: [],
      },
    ],
    links: [],
  };
}

describe("chain_for_card", () => {
  it("returns the chain whose start matches the card", () => {
    const card: DeeplinkCard = {
      title: "now",
      root_situation_id: now_id,
      root_version: 1,
    };
    const chains = [chain(now_id, "now"), chain(other_id, "other")];
    expect(chain_for_card(chains, card)).toEqual(chains[0]);
  });

  it("returns the chain for a case focus", () => {
    const chains = [chain(now_id, "now"), chain(other_id, "other")];
    chains[0] = { ...chains[0], case_id: "case-now" };
    chains[1] = { ...chains[1], case_id: "case-other" };
    expect(
      chain_for_focus(chains, {
        kind: "case",
        case_id: "case-other",
        title: "",
      }),
    ).toBe(chains[1]);
  });

  it("finds a chain from an edge focus", () => {
    const chains = [chain(now_id, "now")];
    chains[0]?.links.push({
      from_situation_id: now_id,
      from_version: 1,
      to_situation_id: other_id,
      to_version: 1,
      p: "0.2000",
      inputs: [],
    });
    expect(
      chain_for_focus(chains, {
        kind: "edge",
        from_situation_id: now_id,
        from_version: 1,
        to_situation_id: other_id,
        to_version: 1,
      }),
    ).toBe(chains[0]);
  });
});
