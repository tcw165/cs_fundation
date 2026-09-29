from pathlib import Path

from agents import Agent

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_case,
    add_terminal_situation,
    get_case,
    lookup_chain_so_far,
    make_deeplink_widget,
    reaches_terminal,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderRequest,
)
from take_home.causal_chains.agents.models.causal_chains.situation import StartSituation
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


causal_chain = Agent[RunContext](
    name="causal_chain",
    instructions=_read_prompt("causal_chain.md"),
    model="gpt-5.6-luna",
    tools=[
        add_case,
        get_case,
        now_scout.as_tool(
            tool_name="now_scout",
            tool_description=(
                "Find the present. Use this once, after the case exists. "
                "It comes back saved as the start."
            ),
        ),
        add_terminal_situation,
        reaches_terminal,
        lookup_chain_so_far,
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Take one step from the current situation toward the future. "
                "Use this after both ends exist, and again until a path runs from the start to the future. "
                "Pass the current situation, the saved future, a direction, and the situation quota that remains. "
                "The direction starts with the case id, then the open line, then the one change. "
                "Either link the current situation to the terminal, "
                "or save one next situation and link the current situation to it."
            ),
            parameters=PathBuilderRequest,
        ),
        make_deeplink_widget,
    ],
    output_type=StartSituation,
)
