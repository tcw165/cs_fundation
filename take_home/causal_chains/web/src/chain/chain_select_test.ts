import { describe, expect, it } from "vitest";

import type { CausalChain, DeeplinkCard } from "./chain_port";
import { chain_for_card } from "./chain_select";

const now_id = "11111111-1111-4111-8111-111111111111";
const other_id = "33333333-3333-4333-8333-333333333333";

function chain(root_id: string, desc: string): CausalChain {
  return {
    situations: [
      {
        situation_id: root_id,
        version: 1,
        desc,
        is_root: true,
      },
    ],
    links: [],
  };
}

describe("chain_for_card", () => {
  it("returns the chain whose root matches the card", () => {
    const card: DeeplinkCard = {
      title: "now",
      root_situation_id: now_id,
      root_version: 1,
    };
    const chains = [chain(now_id, "now"), chain(other_id, "other")];
    expect(chain_for_card(chains, card)).toEqual(chains[0]);
  });
});
