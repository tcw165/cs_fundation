import { useEffect, useState, type ReactNode } from "react";

import { ChainCanvas } from "../chain/chain_canvas";
import { ChainOpenContext } from "../chain/chain_open";
import type { ChainPort, DeeplinkCard } from "../chain/chain_port";
import { Thread } from "../chat/thread";
import type { HealthPort } from "../health/health_port";
import { Rail } from "../shell/rail";

import "../theme/tokens.css";
import "../shell/shell.css";
import "./app.css";

export function AppShell({
  server,
  panel,
  children,
}: {
  server: string;
  panel: ReactNode;
  children: ReactNode;
}) {
  const panel_open = panel !== null;
  return (
    <div className={panel_open ? "shell is-open" : "shell"}>
      <Rail server={server} panel_open={panel_open} />
      <div className="stage">
        <div className="chat-column">{children}</div>
        <div className="panel-slot">{panel}</div>
      </div>
    </div>
  );
}

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
        <AppShell
          server={server}
          panel={
            open_card === null ? null : (
              <ChainCanvas card={open_card} chain_port={chain_port} />
            )
          }
        >
          <Thread />
        </AppShell>
      </main>
    </ChainOpenContext.Provider>
  );
}
