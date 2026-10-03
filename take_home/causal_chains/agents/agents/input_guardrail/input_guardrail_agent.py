from pathlib import Path

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

from take_home.causal_chains.agents.models.causal_chains.input_guardrail_decision import (
    InputGuardrailDecision,
)
from take_home.causal_chains.agents.models.run_context import RunContext


blocked_input_message = "I can only build a causal chain for a hypothetical future."


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


input_guardrail_agent = Agent[RunContext](
    name="input_guardrail",
    instructions=_read_prompt("input_guardrail.md"),
    model="gpt-5.6-luna",
    output_type=InputGuardrailDecision,
)


@input_guardrail(name="input_guardrail", run_in_parallel=False)
async def input_guardrail(
    context: RunContextWrapper[RunContext],
    agent: Agent[RunContext],
    agent_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Block prompt injection and probes for system information before the causal chain starts."""
    del agent
    result = await Runner.run(
        input_guardrail_agent,
        agent_input,
        context=context.context,
    )
    decision = result.final_output_as(InputGuardrailDecision)
    return GuardrailFunctionOutput(
        output_info=decision,
        tripwire_triggered=decision.prompt_injection or decision.system_probe,
    )
