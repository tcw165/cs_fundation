import { useEffect, useState } from "react";

import { chain_for_card } from "./chain_select";
import type { CausalChain, ChainPort, DeeplinkCard } from "./chain_port";

import "./chain.css";

export function ChainCanvas({
  card,
  chain_port,
}: {
  card: DeeplinkCard | null;
  chain_port: ChainPort;
}) {
  const [chain, set_chain] = useState<CausalChain | null>(null);
  const [error, set_error] = useState<string | null>(null);
  const [loaded, set_loaded] = useState(false);

  useEffect(() => {
    if (card === null) {
      set_chain(null);
      set_error(null);
      set_loaded(false);
      return;
    }
    let cancelled = false;
    set_chain(null);
    set_error(null);
    set_loaded(false);
    chain_port
      .get_chains()
      .then((chains) => {
        if (cancelled) {
          return;
        }
        set_chain(chain_for_card(chains, card));
        set_loaded(true);
      })
      .catch((reason: unknown) => {
        if (cancelled) {
          return;
        }
        set_error(reason instanceof Error ? reason.message : "chain failed");
        set_loaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [card, chain_port]);

  if (card === null) {
    return null;
  }
  return (
    <section className="chain-canvas" aria-label="causal chain">
      <h2>{card.title}</h2>
      {error !== null ? <p>{error}</p> : null}
      {error === null && !loaded ? <p>loading</p> : null}
      {error === null && loaded && chain === null ? <p>chain not found</p> : null}
      {chain !== null ? (
        <>
          <ul className="chain-situations">
            {chain.situations.map((situation) => (
              <li key={`${situation.situation_id}:${situation.version}`}>
                v{situation.version} {situation.desc}
              </li>
            ))}
          </ul>
          <ul className="chain-links">
            {chain.links.map((link) => (
              <li
                key={`${link.from_situation_id}:${link.from_version}:${link.to_situation_id}:${link.to_version}`}
              >
                {link.p}
                {link.inputs.length === 0
                  ? ""
                  : ` ${link.inputs
                      .map((input) => `${input.name}=${input.value}`)
                      .join(", ")}`}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
