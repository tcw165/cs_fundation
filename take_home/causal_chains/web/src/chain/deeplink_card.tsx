import type { DataMessagePartProps } from "@assistant-ui/react";
import { useContext } from "react";

import { ChainOpenContext } from "./chain_open";
import type { DeeplinkCard } from "./chain_port";

import "./chain.css";

export function DeeplinkCardButton({
  card,
  on_open,
}: {
  card: DeeplinkCard;
  on_open: (card: DeeplinkCard) => void;
}) {
  return (
    <button
      type="button"
      className="deeplink-card"
      onClick={() => on_open(card)}
    >
      <span className="deeplink-card-title">{card.title}</span>
      <span className="deeplink-card-root">{card.root_situation_id}</span>
      <span className="deeplink-card-version">{card.root_version}</span>
    </button>
  );
}

export function DeeplinkCardPart(props: DataMessagePartProps<DeeplinkCard>) {
  const open_chain = useContext(ChainOpenContext);
  return <DeeplinkCardButton card={props.data} on_open={open_chain} />;
}
