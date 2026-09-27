from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.models.causal_chains.link_inputs import LinkInputs
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


pricer = Agent[RunContext](
    name="pricer",
    instructions=_read_prompt("pricer.md"),
    model="gpt-5.6-luna",
    tools=[WebSearchTool()],
    output_type=LinkInputs,
)
