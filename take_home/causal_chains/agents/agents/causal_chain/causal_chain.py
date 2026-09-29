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
                "Discover the present so the chain has a start. "
                "Use this once, after the case exists and before the future is saved. "
                "Save the present on that case and return the start, including its id and drivers."
            ),
        ),
        add_terminal_situation,
        reaches_terminal,
        lookup_chain_so_far,
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Explore the next mid-chain situation from the current one, "
                "to grow the path toward the future. "
                "Either link the current situation to the terminal, "
                "or save one next situation and link the current situation to it."
            ),
            parameters=PathBuilderRequest,
        ),
        make_deeplink_widget,
    ],
    output_type=StartSituation,
)
