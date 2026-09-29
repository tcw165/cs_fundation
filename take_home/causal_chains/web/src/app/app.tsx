import { useEffect, useRef, useState, type ReactNode } from "react";

import { ChainCanvas } from "../chain/chain_canvas";
import type { ChainPort } from "../chain/chain_port";
import { card_from_focus, folded_panel, panel_from_link, type PanelState } from "../chain/panel_state";
import { Thread } from "../chat/thread";
import type { ChatPort } from "../chat/chat_port";
import type { RevealTiming } from "../chat/reveal_timing";
import { use_chat_session } from "../chat/use_chat_session";
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
  chat_port,
  conversation_id,
  timing,
}: {
  health_port: HealthPort;
  chain_port: ChainPort;
  chat_port: ChatPort;
  conversation_id: string;
  timing: RevealTiming;
}) {
  const [server, set_server] = useState("loading");
  const [panel, set_panel] = useState<PanelState>(folded_panel);
  const opened_links = useRef(new Set<string>());
  const session = use_chat_session(chat_port, conversation_id, timing);

  useEffect(() => {
    health_port
      .get_health()
      .then((report) => set_server(report.status))
      .catch(() => set_server("down"));
  }, [health_port]);

  useEffect(() => {
    for (const item of session.state.shown) {
      if (item.type !== "deeplink" || opened_links.current.has(item.message_id)) {
        continue;
      }
      opened_links.current.add(item.message_id);
      const next = panel_from_link(item.link);
      if (next !== null) {
        set_panel(next);
      }
    }
  }, [session.state.shown]);

  const card = card_from_focus(panel.focus);
  return (
    <main className="app">
      <AppShell
        server={server}
        panel={
          panel.open && card !== null ? (
            <ChainCanvas card={card} chain_port={chain_port} />
          ) : null
        }
      >
        <Thread
          session={session}
          on_open_link={(link) => {
            const next = panel_from_link(link);
            if (next !== null) {
              set_panel(next);
            }
          }}
        />
      </AppShell>
    </main>
  );
}
