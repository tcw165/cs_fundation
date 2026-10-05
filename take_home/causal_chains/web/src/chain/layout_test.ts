import { describe, expect, it } from "vitest";

import type { CausalChain } from "./chain_port";
import { NODE_HEIGHT, NODE_HEIGHT_OPEN, layout_chain } from "./layout";

const chain: CausalChain = {
  situations: [
    {
      situation_id: "start",
      version: 1,
      created_timestamp: "2026-10-01T00:00:00+00:00",
      kind: "start",
      title: "Strait shut",
      desc: "strait shut",
      remained_drivers: [],
    },
    {
      situation_id: "step",
      version: 1,
      created_timestamp: "2026-10-01T00:00:00+00:00",
      kind: "situation",
      title: "Talks",
      desc: "talks",
      remained_drivers: [],
    },
    {
      situation_id: "end",
      version: 1,
      created_timestamp: "2026-10-01T00:00:00+00:00",
      kind: "terminal",
      title: "Open",
      desc: "open",
      remained_drivers: [],
    },
  ],
  links: [
    {
      from_situation_id: "start",
      from_version: 1,
      to_situation_id: "step",
      to_version: 1,
      p: "0.4000",
      inputs: [{ name: "talks", desc: "Talks this week.", probability: 0.4 }],
    },
    {
      from_situation_id: "step",
      from_version: 1,
      to_situation_id: "end",
      to_version: 1,
      p: "0.8000",
      inputs: [{ name: "transit", desc: "Ships in transit.", probability: 0.8 }],
    },
  ],
};

describe("layout_chain", () => {
  it("pushes later nodes down when a situation card opens", () => {
    const closed = layout_chain(chain, null);
    const open = layout_chain(chain, { kind: "situation", situation_id: "start", version: 1 });
    const closed_step = closed.nodes.find((node) => node.situation_id === "step");
    const open_start = open.nodes.find((node) => node.situation_id === "start");
    const open_step = open.nodes.find((node) => node.situation_id === "step");
    expect(open_start?.height).toBe(NODE_HEIGHT_OPEN);
    expect(closed.nodes[0]?.height).toBe(NODE_HEIGHT);
    expect(open_step && closed_step ? open_step.y : 0).toBeGreaterThan(closed_step?.y ?? 0);
  });

  it("inserts a scrolling edge card between the two situations", () => {
    const closed = layout_chain(chain, null);
    const open = layout_chain(chain, {
      kind: "edge",
      from_situation_id: "start",
      from_version: 1,
      to_situation_id: "step",
      to_version: 1,
    });
    const edge = open.edges.find((item) => item.from_situation_id === "start");
    const closed_step = closed.nodes.find((node) => node.situation_id === "step");
    const open_step = open.nodes.find((node) => node.situation_id === "step");
    expect(edge?.card).not.toBeNull();
    expect(edge?.expanded).toBe(true);
    expect(open_step && closed_step ? open_step.y : 0).toBeGreaterThan(closed_step?.y ?? 0);
  });

  it("places a fork side by side and the shared terminal below both", () => {
    const branched: CausalChain = {
      situations: [
        { ...chain.situations[0], situation_id: "start", title: "Start" },
        { ...chain.situations[1], situation_id: "left", title: "Left" },
        { ...chain.situations[1], situation_id: "right", title: "Right" },
        { ...chain.situations[2], situation_id: "end", title: "End" },
      ],
      links: [
        { ...chain.links[0], to_situation_id: "left" },
        { ...chain.links[0], to_situation_id: "right" },
        { ...chain.links[1], from_situation_id: "left" },
        { ...chain.links[1], from_situation_id: "right" },
      ],
    };
    const layout = layout_chain(branched, null);
    const start = layout.nodes.find((node) => node.situation_id === "start");
    const left = layout.nodes.find((node) => node.situation_id === "left");
    const right = layout.nodes.find((node) => node.situation_id === "right");
    const end = layout.nodes.find((node) => node.situation_id === "end");
    const linear = layout_chain(chain, null);
    expect(new Set(linear.nodes.map((node) => node.x)).size).toBe(1);
    expect(left?.y).toBe(right?.y);
    expect(left && right ? left.x : 0).toBeLessThan(right?.x ?? 0);
    expect(start && left ? start.y : 0).toBeLessThan(left?.y ?? 0);
    expect(end && left ? end.y : 0).toBeGreaterThan(left?.y ?? 0);
    expect(start && left && right ? start.x : 0).toBeGreaterThan(left?.x ?? 0);
    expect(start && left && right ? start.x : 1).toBeLessThan(right?.x ?? 0);
    expect(layout.width).toBeGreaterThan(linear.width);
    expect(layout.edges).toHaveLength(4);
  });
});
