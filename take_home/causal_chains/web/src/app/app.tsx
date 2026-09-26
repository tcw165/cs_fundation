import { useEffect, useState } from "react";

import { Thread } from "../chat/thread";
import type { HealthPort } from "../health/health_port";

import "./app.css";

export function App({ health_port }: { health_port: HealthPort }) {
  const [db, set_db] = useState("loading");
  useEffect(() => {
    health_port
      .get_health()
      .then((report) => set_db(report.db))
      .catch(() => set_db("down"));
  }, [health_port]);
  return (
    <main className="app">
      <header className="app-header">
        <h1>causal_chains</h1>
      </header>
      <Thread />
      <footer className="app-footer">db: {db}</footer>
    </main>
  );
}
