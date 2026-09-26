import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/app";
import { create_health_http } from "./health/health_http";

const api_url = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const health_port = create_health_http(api_url);
const root = document.getElementById("root");
if (!root) {
  throw new Error("root element missing");
}
createRoot(root).render(
  <StrictMode>
    <App health_port={health_port} />
  </StrictMode>,
);
