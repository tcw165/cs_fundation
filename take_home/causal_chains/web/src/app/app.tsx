import { useEffect, useState } from "react";

import type { HealthPort } from "../health/health_port";

export function App({ health_port }: { health_port: HealthPort }) {
  const [db, set_db] = useState("loading");
  useEffect(() => {
    health_port
      .get_health()
      .then((report) => set_db(report.db))
      .catch(() => set_db("down"));
  }, [health_port]);
  return (
    <main>
      <h1>causal_chains</h1>
      <p>db: {db}</p>
    </main>
  );
}
