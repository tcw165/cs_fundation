// @vitest-environment jsdom

import type { ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { act } from "react";
import { describe, expect, it, vi } from "vitest";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

import { ChainCanvas, chain_poll_ms } from "./chain_canvas";
import type { ChainPort } from "./chain_port";
import type { FocusTarget } from "./panel_state";

const now_id = "11111111-1111-4111-8111-111111111111";
const next_id = "22222222-2222-4222-8222-222222222222";

const focus: FocusTarget = {
  kind: "chain",
  root_situation_id: now_id,
  root_version: 1,
  title: "now",
};

function render(node: ReactElement): { host: HTMLDivElement; root: Root } {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  act(() => {
    root.render(node);
  });
  return { host, root };
}

function y_of(host: HTMLElement, situation_id: string): number {
  const node = host.querySelector(`[data-situation-id="${situation_id}"]`);
  return Number(node?.getAttribute("data-y") ?? "0");
}

describe("chain canvas", () => {
  it("opens a situation card and an edge card, pushing the nodes apart", async () => {
    const get_chains = vi.fn<ChainPort["get_chains"]>().mockResolvedValue([
      {
        situations: [
          {
            situation_id: now_id,
            version: 1,
            title: "Strait shut",
            desc: "strait shut for a long stretch of text that should remain readable inside the scrolling card when the situation is expanded beyond the collapsed summary line",
            remained_drivers: [],
            potential_drivers: ["blockade", "insurance", "naval warning"],
          },
          {
            situation_id: next_id,
            version: 1,
            title: "Talks start",
            desc: "talks start",
            remained_drivers: [],
          },
        ],
        links: [
          {
            from_situation_id: now_id,
            from_version: 1,
            to_situation_id: next_id,
            to_version: 1,
            p: "0.0800",
            inputs: [
              { name: "deal_odds", desc: "Odds of a deal.", probability: 0.08 },
            ],
          },
        ],
      },
    ]);
    const chain_port: ChainPort = { get_chains };
    const { host, root } = render(<ChainCanvas focus={focus} chain_port={chain_port} />);
    expect(host.querySelector(".chain-canvas")).not.toBeNull();
    await act(async () => {
      await Promise.resolve();
    });
    expect(get_chains).toHaveBeenCalledTimes(1);
    expect(host.querySelectorAll(".overview-node.is-latest")).toHaveLength(2);
    expect(host.querySelector(`[data-situation-id="${now_id}"]`)?.getAttribute("data-open")).toBe(
      "true",
    );
    expect(host.querySelector(".node-title")?.textContent).toBe("Strait shut");
    expect(host.textContent).toContain(
      "strait shut for a long stretch of text that should remain readable",
    );
    const open_y = y_of(host, next_id);
    const toggle = host.querySelector(".node-toggle");
    await act(async () => {
      toggle?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(host.querySelector(`[data-situation-id="${now_id}"]`)?.getAttribute("data-open")).toBe(
      "false",
    );
    expect(y_of(host, next_id)).toBeLessThan(open_y);
    const collapsed_y = y_of(host, next_id);
    const edge = host.querySelector("button[aria-label='Open link 0.0800']");
    await act(async () => {
      edge?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(host.textContent).toContain("deal_odds");
    expect(host.textContent).toContain("very unlikely");
    expect(y_of(host, next_id)).toBeGreaterThan(collapsed_y);
    expect(host.querySelector(".edge-card.is-open")).not.toBeNull();
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("keeps older cases dim and marks the open case", async () => {
    const older_id = "33333333-3333-4333-8333-333333333333";
    const get_chains = vi.fn<ChainPort["get_chains"]>().mockResolvedValue([
      {
        case_id: "older",
        situations: [
          {
            situation_id: older_id,
            version: 1,
            title: "Older start",
            desc: "older start",
            remained_drivers: [],
            potential_drivers: ["then"],
          },
        ],
        links: [],
      },
      {
        case_id: "opened",
        situations: [
          {
            situation_id: now_id,
            version: 1,
            title: "Strait shut",
            desc: "strait shut",
            remained_drivers: [],
            potential_drivers: ["blockade"],
          },
        ],
        links: [],
      },
    ]);
    const chain_port: ChainPort = { get_chains };
    const { host, root } = render(<ChainCanvas focus={focus} chain_port={chain_port} />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(host.querySelectorAll(".overview-node")).toHaveLength(2);
    expect(host.querySelectorAll(".overview-node.is-latest")).toHaveLength(1);
    expect(host.querySelector(".overview-node.is-latest")?.getAttribute("data-latest")).toBe(
      "true",
    );
    act(() => {
      root.unmount();
    });
    host.remove();
  });

  it("polls again after a failed load and draws the chain when the db returns", async () => {
    vi.useFakeTimers();
    const get_chains = vi
      .fn<ChainPort["get_chains"]>()
      .mockRejectedValueOnce(new Error("Failed to fetch"))
      .mockResolvedValueOnce([
        {
          situations: [
            {
              situation_id: now_id,
              version: 1,
              title: "Strait shut",
              desc: "strait shut",
              remained_drivers: [],
              potential_drivers: ["blockade"],
            },
          ],
          links: [],
        },
      ]);
    const chain_port: ChainPort = { get_chains };
    const { host, root } = render(<ChainCanvas focus={focus} chain_port={chain_port} />);
    await act(async () => {
      await Promise.resolve();
    });
    expect(host.textContent).toContain("Failed to fetch");
    expect(host.querySelector(".graph-canvas")).toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(chain_poll_ms);
    });
    expect(get_chains).toHaveBeenCalledTimes(2);
    expect(host.textContent).not.toContain("Failed to fetch");
    expect(host.querySelector(".graph-canvas")).not.toBeNull();
    act(() => {
      root.unmount();
    });
    host.remove();
    vi.useRealTimers();
  });
});
