import type { CausalChain, DeeplinkCard } from "./chain_port";

export function chain_for_card(
  chains: CausalChain[],
  card: DeeplinkCard,
): CausalChain | null {
  for (const chain of chains) {
    const root = chain.situations.find((situation) => situation.is_root);
    if (
      root !== undefined &&
      root.situation_id === card.root_situation_id &&
      root.version === card.root_version
    ) {
      return chain;
    }
  }
  return null;
}
