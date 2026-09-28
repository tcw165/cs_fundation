from pathlib import Path

from agents import Agent

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
    make_deeplink_widget,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


causal_chain = Agent[RunContext](
    name="causal_chain",
    instructions=_read_prompt("causal_chain.md"),
    model="gpt-5.6-luna",
    tools=[
        now_scout.as_tool(
            tool_name="now_scout",
            tool_description=(
                "Discover the present so the chain has a place to start. "
                "Use this once, before any next situation. "
                "Save the present and return that situation, including its id."
            ),
        ),
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Explore the next situations from the current one, to grow the path toward the future. "
                "Use this after the present is saved, and again from the situation you just linked. "
                "Save the next situations from the current description "
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
        add_situation,
        link_situations,
        make_deeplink_widget,
    ],
    output_type=Situation,
)
