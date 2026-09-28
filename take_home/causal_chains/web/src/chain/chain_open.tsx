import { createContext } from "react";

import type { DeeplinkCard } from "./chain_port";

export const ChainOpenContext = createContext<(card: DeeplinkCard) => void>(
  () => {},
);
