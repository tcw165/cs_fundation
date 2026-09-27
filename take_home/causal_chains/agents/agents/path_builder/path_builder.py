from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.unpriced_chain import UnpricedChain
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


path_builder = Agent[RunContext](
    name="path_builder",
    instructions=_read_prompt("path_builder.md"),
    model="gpt-5.6-luna",
    tools=[WebSearchTool()],
    output_type=UnpricedChain,
)
