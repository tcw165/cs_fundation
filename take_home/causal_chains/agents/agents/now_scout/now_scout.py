from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.models.database.situation import Situation
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


now_scout = Agent[RunContext](
    name="now_scout",
    instructions=_read_prompt("now_scout.md"),
    model="gpt-5.6-luna",
    tools=[WebSearchTool()],
    output_type=Situation,
)
