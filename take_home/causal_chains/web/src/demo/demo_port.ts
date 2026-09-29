import type { ChainPort } from "../chain/chain_port";
import type { ChatPort, Message } from "../chat/chat_port";
import { hormuz_chain, hormuz_messages } from "./hormuz_fixture";

export function create_demo_chat_port(): ChatPort {
  return {
    post_message: async ({ text }) => ({
      turn_id: "demo",
      conversation_id: "1",
      status: "done",
      from_message: text,
    }),
    subscribe_turn: async function* (): AsyncGenerator<Message> {
      for (const message of hormuz_messages) {
        yield message;
      }
    },
  };
}

export function create_demo_chain_port(): ChainPort {
  return {
    get_chains: async () => [hormuz_chain],
  };
}
