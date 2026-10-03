from pathlib import Path

from agents import Agent, handoff

from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (  # pragma: allowlist secret
    causal_chain,
)
from take_home.causal_chains.agents.agents.input_guardrail.input_guardrail_agent import (  # pragma: allowlist secret
    input_guardrail,
)
from take_home.causal_chains.agents.models.run_context import RunContext  # pragma: allowlist secret


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


chief_of_staff = Agent[RunContext](
    name="chief_of_staff",
    instructions=_read_prompt("chief_of_staff.md"),
    model="gpt-5.6-luna",
    handoffs=[
        handoff(
            causal_chain,
            tool_description_override=(
                "Work with the helper who connects now to a hypothetical future. "
                "Use this when the person asks a hypothetical question "
                "or wants to explore a causal chain. "
                "Hand them the question. Do not build the chain yourself."
            ),
        ),
    ],
    input_guardrails=[input_guardrail],
    output_type=str,
)
