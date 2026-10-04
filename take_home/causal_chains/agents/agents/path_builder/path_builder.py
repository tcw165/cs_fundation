from pathlib import Path

from agents import Agent, ModelSettings, WebSearchTool
from openai.types.shared.reasoning import Reasoning

from take_home.causal_chains.agents.agent_run_config.agent_run_config import (
    decorate_tail_messages,
)
from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
)
from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderResult,
)
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


path_builder = Agent[RunContext](
    name="path_builder",
    instructions=_read_prompt("path_builder.md"),
    model="gpt-5.6-luna",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),
        verbosity="low",
    ),
    tools=[
        WebSearchTool(),
        add_situation,
        pricer.as_tool(
            tool_name="pricer",
            tool_description=(
                "Decide what a person could move on one link, so the chain can store how likely that step is. "
                "Use this once for the link you are about to save, "
                "from the current situation to the next situation or to the terminal. "
                "Name the input variables on that link."
            ),
            run_config=decorate_tail_messages(),
        ),
        link_situations,
    ],
    output_type=PathBuilderResult,
)
