import type { CausalChain, DeeplinkCard } from "./chain_port";
import type { FocusTarget } from "./panel_state";

export function chain_for_card(
  chains: CausalChain[],
  card: DeeplinkCard,
): CausalChain | null {
  for (const chain of chains) {
    const start = chain.situations.find(
      (situation) => situation.potential_factors !== undefined,
    );
    if (
      start !== undefined &&
      start.situation_id === card.root_situation_id &&
      start.version === card.root_version
    ) {
      return chain;
    }
  }
  return null;
}

export function chain_for_focus(
  chains: CausalChain[],
  focus: FocusTarget,
): CausalChain | null {
  if (focus.kind === "chain") {
    return chain_for_card(chains, {
      title: focus.title,
      root_situation_id: focus.root_situation_id,
      root_version: focus.root_version,
    });
  }
  if (focus.kind === "situation") {
    return (
      chains.find((chain) =>
        chain.situations.some(
          (situation) =>
            situation.situation_id === focus.situation_id &&
            situation.version === focus.version,
        ),
      ) ?? null
    );
  }
  return (
    chains.find((chain) =>
      chain.links.some(
        (link) =>
          link.from_situation_id === focus.from_situation_id &&
          link.from_version === focus.from_version &&
          link.to_situation_id === focus.to_situation_id &&
          link.to_version === focus.to_version,
      ),
    ) ?? null
  );
}
