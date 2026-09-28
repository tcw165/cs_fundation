import type { CausalChain, DeeplinkCard } from "./chain_port";

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
