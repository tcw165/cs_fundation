import { StrictMode, useMemo } from "react";
import { createRoot } from "react-dom/client";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
} from "@assistant-ui/react";

import { App } from "./app/app";
import { create_chat_http } from "./chat/chat_http";
import { create_chat_model_adapter } from "./chat/chat_model_adapter";
import { create_health_http } from "./health/health_http";

const api_url = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const conversation_id = "1";
const health_port = create_health_http(api_url);
const chat_port = create_chat_http(api_url);

function Root() {
  const adapter = useMemo(
    () => create_chat_model_adapter(chat_port, conversation_id),
    [],
  );
  const runtime = useLocalRuntime(adapter);
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <App health_port={health_port} />
    </AssistantRuntimeProvider>
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
