from pathlib import Path

from agents import Agent, handoff

from take_home.causal_chains.agents.agent_tools.conversation_tools import (
    build_conversation_tools,
)
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (  # pragma: allowlist secret
    causal_chain,
)
from take_home.causal_chains.agents.agents.input_guardrail.input_guardrail_agent import (  # pragma: allowlist secret
    input_guardrail,
)
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.time.protocol.protocol import Clock


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


def build_chief_of_staff(
    conversation_id: str,
    messaging_store: MessagingStore,
    clock: Clock,
) -> Agent[RunContext]:
    return Agent[RunContext](
        name="chief_of_staff",
        instructions=_read_prompt("chief_of_staff.md"),
        model="gpt-5.6-luna",
        tools=[
            *build_conversation_tools(
                conversation_id=conversation_id,
                messaging_store=messaging_store,
                clock=clock,
            ),
        ],
        handoffs=[
            handoff(
                causal_chain,
                tool_description_override=(
                    "Work with the helper who connects now to a hypothetical future. "
                    "Use this when the latest user message states a future change, "
                    "even if the wording is messy, terse, or missing what happens. "
                    "Hand them the question as written. Do not build the chain yourself."
                ),
            ),
        ],
        input_guardrails=[input_guardrail],
        output_type=str,
    )
