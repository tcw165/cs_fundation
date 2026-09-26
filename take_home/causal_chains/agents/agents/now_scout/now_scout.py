from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.models.database.situation import Situation


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


now_scout = Agent(
    name="now_scout",
    instructions=_read_prompt("now_scout.md"),
    model="gpt-5.6-luna",
    tools=[WebSearchTool()],
    output_type=Situation,
)
