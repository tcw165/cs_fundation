import { useEffect, useState } from "react";

import { ChainCanvas } from "../chain/chain_canvas";
import { ChainOpenContext } from "../chain/chain_open";
import type { ChainPort, DeeplinkCard } from "../chain/chain_port";
import { Thread } from "../chat/thread";
import type { HealthPort } from "../health/health_port";

import "./app.css";

export function App({
  health_port,
  chain_port,
}: {
  health_port: HealthPort;
  chain_port: ChainPort;
}) {
  const [server, set_server] = useState("loading");
  const [open_card, set_open_card] = useState<DeeplinkCard | null>(null);
  useEffect(() => {
    health_port
      .get_health()
      .then((report) => set_server(report.status))
      .catch(() => set_server("down"));
  }, [health_port]);
  return (
    <ChainOpenContext.Provider value={set_open_card}>
      <main className="app">
        <header className="app-header">
          <h1>causal_chains</h1>
        </header>
        <Thread />
        <ChainCanvas card={open_card} chain_port={chain_port} />
        <footer className="app-footer">server: {server}</footer>
      </main>
    </ChainOpenContext.Provider>
  );
}
