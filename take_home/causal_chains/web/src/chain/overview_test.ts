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
        kind: "start",
        title: situation_id,
        desc: situation_id,
        remained_drivers: [],
      },
      {
        situation_id: `${situation_id}-next`,
        version: 1,
        created_timestamp: "2026-10-01T00:00:00+00:00",
        kind: "situation",
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

  it("stacks a fork on two lanes", () => {
    const forked = chain("fork", "case-fork");
    forked.situations.push({
      situation_id: "fork-other",
      version: 1,
      created_timestamp: "2026-10-01T00:00:00+00:00",
      kind: "situation",
      title: "other",
      desc: "other",
      remained_drivers: [],
    });
    forked.links.push({
      from_situation_id: "fork",
      from_version: 1,
      to_situation_id: "fork-other",
      to_version: 1,
      p: "0.5",
      inputs: [],
    });
    const layout = layout_overview([forked], forked);
    const branch = layout.nodes.filter((node) => node.cx === layout.nodes[1]?.cx);
    expect(branch).toHaveLength(2);
    expect(branch[0]?.cy).not.toBe(branch[1]?.cy);
  });
});
