// @vitest-environment jsdom

import { useState, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { act } from "react";
import { describe, expect, it, vi } from "vitest";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

import { ChainCanvas } from "./chain_canvas";
import { DeeplinkCardButton } from "./deeplink_card";
import type { ChainPort, DeeplinkCard } from "./chain_port";

const card: DeeplinkCard = {
  title: "now",
  root_situation_id: "11111111-1111-4111-8111-111111111111",
  root_version: 1,
};

function render(node: ReactNode): { host: HTMLDivElement; root: Root } {
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  act(() => {
    root.render(node);
  });
  return { host, root };
}

function Harness({ chain_port }: { chain_port: ChainPort }) {
  const [open_card, set_open_card] = useState<DeeplinkCard | null>(null);
  return (
    <>
      <DeeplinkCardButton card={card} on_open={set_open_card} />
      <ChainCanvas card={open_card} chain_port={chain_port} />
    </>
  );
}

describe("chain canvas", () => {
  it("stays closed until the deeplink card is clicked", async () => {
    const get_chains = vi.fn<ChainPort["get_chains"]>().mockResolvedValue([
      {
        situations: [
          {
            situation_id: card.root_situation_id,
            version: 1,
            desc: "strait shut",
            is_root: true,
            is_end: false,
          },
        ],
        links: [
          {
            from_situation_id: card.root_situation_id,
            from_version: 1,
            to_situation_id: "22222222-2222-4222-8222-222222222222",
            to_version: 1,
            p: "0.0800",
            inputs: [{ name: "deal_odds", value: "0.08" }],
          },
        ],
      },
    ]);
    const chain_port: ChainPort = { get_chains };
    const closed = render(<ChainCanvas card={null} chain_port={chain_port} />);
    expect(closed.host.querySelector(".chain-canvas")).toBeNull();
    expect(get_chains).not.toHaveBeenCalled();
    act(() => {
      closed.root.unmount();
    });

    const { host, root } = render(<Harness chain_port={chain_port} />);
    expect(host.querySelector(".chain-canvas")).toBeNull();
    const button = host.querySelector("button");
    expect(button?.textContent).toContain("now");
    expect(button?.textContent).toContain(card.root_situation_id);
    expect(button?.textContent).toContain("1");
    await act(async () => {
      button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    expect(get_chains).toHaveBeenCalledTimes(1);
    expect(host.textContent).toContain("strait shut");
    expect(host.textContent).toContain("0.0800");
    expect(host.textContent).toContain("deal_odds=0.08");
    act(() => {
      root.unmount();
    });
  });
});
