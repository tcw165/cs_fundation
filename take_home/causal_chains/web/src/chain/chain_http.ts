import type { CausalChain, ChainPort } from "./chain_port";

export function create_chain_http(api_url: string): ChainPort {
  return {
    get_chains: async () => {
      const response = await fetch(`${api_url}/causal_chains`);
      if (!response.ok) {
        throw new Error(`get_chains failed: ${response.status}`);
      }
      return (await response.json()) as CausalChain[];
    },
  };
}
