from pathlib import Path

from agents import Agent, ModelSettings, WebSearchTool
from openai.types.shared.reasoning import Reasoning

from take_home.causal_chains.agents.agent_tools.chain_tools import add_start_situation
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


now_scout = Agent[RunContext](
    name="now_scout",
    instructions=_read_prompt("now_scout.md"),
    model="gpt-5.6-luna",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),
        verbosity="low",
    ),
    tools=[
        WebSearchTool(),
        add_start_situation,
    ],
    output_type=Situation,
)
