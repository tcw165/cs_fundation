import { useEffect, useState } from "react";

import { Thread } from "../chat/thread";
import type { HealthPort } from "../health/health_port";

import "./app.css";

export function App({ health_port }: { health_port: HealthPort }) {
  const [server, set_server] = useState("loading");
  useEffect(() => {
    health_port
      .get_health()
      .then((report) => set_server(report.status))
      .catch(() => set_server("down"));
  }, [health_port]);
  return (
    <main className="app">
      <header className="app-header">
        <h1>causal_chains</h1>
      </header>
      <Thread />
      <footer className="app-footer">server: {server}</footer>
    </main>
  );
}
