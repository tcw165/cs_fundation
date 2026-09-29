// @vitest-environment jsdom

import type { ReactElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { act } from "react";
import { describe, expect, it, vi } from "vitest";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

import { ChainCanvas } from "./chain_canvas";
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
            desc: "strait shut for a long stretch of text that should remain readable inside the scrolling card when the situation is expanded beyond the collapsed summary line",
            potential_factors: ["blockade", "insurance", "naval warning"],
          },
          {
            situation_id: next_id,
            version: 1,
            desc: "talks start",
          },
        ],
        links: [
          {
            from_situation_id: now_id,
            from_version: 1,
            to_situation_id: next_id,
            to_version: 1,
            p: "0.0800",
            inputs: [{ name: "deal_odds", value: "0.08" }],
          },
        ],
      },
    ]);
    const chain_port: ChainPort = { get_chains };
    const { host, root } = render(
      <ChainCanvas focus={focus} focus_token={1} chain_port={chain_port} />,
    );
    expect(host.querySelector(".chain-canvas")).not.toBeNull();
    await act(async () => {
      await Promise.resolve();
    });
    expect(get_chains).toHaveBeenCalledTimes(1);
    expect(host.querySelector(`[data-situation-id="${now_id}"]`)?.getAttribute("data-open")).toBe(
      "true",
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
});