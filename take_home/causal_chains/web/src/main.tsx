import "@fontsource/instrument-serif/400.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/app";
import { create_chain_http } from "./chain/chain_http";
import { create_chat_http } from "./chat/chat_http";
import { fast_timing, studio_timing } from "./chat/reveal_timing";
import { create_demo_chain_port, create_demo_chat_port } from "./demo/demo_port";
import { create_health_http } from "./health/health_http";

const api_url = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const params = new URLSearchParams(window.location.search);
const timing = params.get("pace") === "fast" ? fast_timing : studio_timing;
const demo = params.has("demo");
const health_port = create_health_http(api_url);
const chat_port = demo ? create_demo_chat_port() : create_chat_http(api_url);
const chain_port = demo ? create_demo_chain_port() : create_chain_http(api_url);

function Root() {
  return (
    <App
      health_port={health_port}
      chat_port={chat_port}
      chain_port={chain_port}
      conversation_id="1"
      timing={timing}
    />
  );
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("root element missing");
}
createRoot(root).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
