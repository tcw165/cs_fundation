import type { CausalChain } from "../chain/chain_port";
import type { Message } from "../chat/chat_port";

export const hormuz_start_id = "99b353e5-0f01-4fcc-b78e-89b1b4233f46";
const agreement_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1";
const security_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2";
const open_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3";

export const hormuz_title =
  "As of September 29, 2026, the Strait of Hormuz is not yet confirmed open to normal commercial transit.";

export const hormuz_chain: CausalChain = {
  situations: [
    {
      situation_id: hormuz_start_id,
      version: 1,
      desc: "The Strait of Hormuz is not confirmed open. Safe passage, unrestricted vessel movement, and the lifting of restrictions are still unresolved. Insurers are pricing war risk, naval warnings remain active, and commercial schedules are slipping day by day while governments argue over what an open strait would even mean.",
      potential_factors: [
        "naval interdiction",
        "war-risk insurance",
        "diplomatic channel",
        "mine clearance",
        "flag-state guidance",
        "spare tanker capacity",
      ],
    },
    {
      situation_id: agreement_id,
      version: 1,
      desc: "Diplomatic talks produce a credible de-escalation agreement that both coast guards can brief to ship captains.",
    },
    {
      situation_id: security_id,
      version: 1,
      desc: "Attacks stop, warnings are withdrawn, and a verified safe-transit procedure replaces the standing restriction.",
    },
    {
      situation_id: open_id,
      version: 1,
      desc: "Scheduled commercial vessels pass safely and the Strait of Hormuz is open to normal shipping.",
      original_ask: "The Strait of Hormuz is going to open next week.",
    },
  ],
  links: [
    {
      from_situation_id: hormuz_start_id,
      from_version: 1,
      to_situation_id: agreement_id,
      to_version: 1,
      p: "0.4200",
      inputs: [
        { name: "talks_hold", value: "0.55" },
        { name: "public_commitment", value: "0.29" },
      ],
    },
    {
      from_situation_id: agreement_id,
      from_version: 1,
      to_situation_id: security_id,
      to_version: 1,
      p: "0.6100",
      inputs: [
        { name: "attacks_cease", value: "0.70" },
        { name: "warnings_withdrawn", value: "0.52" },
      ],
    },
    {
      from_situation_id: security_id,
      from_version: 1,
      to_situation_id: open_id,
      to_version: 1,
      p: "0.1800",
      inputs: [
        { name: "transit_clearance", value: "0.22" },
        { name: "insurer_cover", value: "0.14" },
      ],
    },
  ],
};

export function hormuz_deeplink(): string {
  const params = new URLSearchParams({
    root_situation_id: hormuz_start_id,
    root_version: "1",
    title: hormuz_title,
  });
  return `causal_chains://chain?${params.toString()}`;
}

export const hormuz_messages: Message[] = [
  {
    type: "markdown",
    message_id: "m_create",
    role: "agent",
    text: "Creating a case, then I'll identify the present state that could lead to the stated future.",
  },
  { type: "heartbeat", message_id: "m_beat_1", role: "meta" },
  {
    type: "markdown",
    message_id: "m_save",
    role: "agent",
    text: "Saving both ends of the scenario: the present as the start, and the forecast about the Strait opening next week as the terminal situation.",
  },
  { type: "heartbeat", message_id: "m_beat_2", role: "meta" },
  {
    type: "deeplink",
    message_id: "m_link",
    role: "other",
    link: hormuz_deeplink(),
  },
  {
    type: "markdown",
    message_id: "m_close",
    role: "agent",
    text: "Diplomatic talks produce an agreement, verified security measures follow, and commercial vessels then test the reopened strait.",
  },
];
