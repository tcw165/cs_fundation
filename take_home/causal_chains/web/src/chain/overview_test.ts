import { describe, expect, it } from "vitest";

import type { CausalChain } from "./chain_port";
import { layout_overview } from "./overview";

function chain(situation_id: string, case_id: string): CausalChain {
  return {
    case_id,
    situations: [
      {
        situation_id,
        version: 1,
        created_timestamp: "2026-10-01T00:00:00+00:00",
        title: situation_id,
        desc: situation_id,
        remained_drivers: [],
        potential_drivers: ["now"],
      },
      {
        situation_id: `${situation_id}-next`,
        version: 1,
        created_timestamp: "2026-10-01T00:00:00+00:00",
        title: "next",
        desc: "next",
        remained_drivers: [],
      },
    ],
    links: [
      {
        from_situation_id: situation_id,
        from_version: 1,
        to_situation_id: `${situation_id}-next`,
        to_version: 1,
        p: "0.5",
        inputs: [],
      },
    ],
  };
}

describe("layout_overview", () => {
  it("draws every case and marks the open one", () => {
    const older = chain("older", "case-old");
    const opened = chain("opened", "case-new");
    const layout = layout_overview([older, opened], opened);
    expect(layout.nodes).toHaveLength(4);
    expect(layout.edges).toHaveLength(2);
    expect(layout.nodes.filter((node) => node.latest)).toHaveLength(2);
    expect(layout.edges.filter((edge) => edge.latest)).toHaveLength(1);
    expect(layout.nodes.filter((node) => !node.latest)).toHaveLength(2);
  });
});
