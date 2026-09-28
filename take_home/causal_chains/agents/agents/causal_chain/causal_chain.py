from pathlib import Path

from agents import Agent

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_case,
    add_terminal_situation,
    get_case,
    link_situations,
    lookup_leaf_situations,
    make_deeplink_widget,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.agents.pricer.pricer import pricer
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
        lookup_leaf_situations,
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Explore the next mid-chain situations from the current one, to grow the path toward the future. "
                "Use this after both ends exist, and again from a leaf, or from the start when there is no leaf. "
                "Save the next situations on the case from the current description "
                "and the thoughts about remaining attempts, and return them."
            ),
        ),
        pricer.as_tool(
            tool_name="pricer",
            tool_description=(
                "Decide what a person could move on one link, so the chain can store how likely that step is. "
                "Use this for every next situation, in the same step you save the link. "
                "Name the input variables on the link from the current situation "
                "to one next situation."
            ),
        ),
        link_situations,
        make_deeplink_widget,
    ],
    output_type=StartSituation,
)
