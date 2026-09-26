from pathlib import Path

from agents import Agent

from take_home.causal_chains.agents.agents.crystal_ball.chain_graph import ChainGraph
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.agents.pricer.pricer import pricer


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


crystal_ball = Agent(
    name="crystal_ball",
    instructions=_read_prompt("crystal_ball.md"),
    model="gpt-5.6-luna",
    tools=[
        now_scout.as_tool(
            tool_name="now_scout",
            tool_description="Write the root situation from the live present.",
        ),
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description="Build the paths from that root to the query.",
        ),
        pricer.as_tool(
            tool_name="pricer",
            tool_description="Set a probability on every edge.",
        ),
    ],
    output_type=ChainGraph,
)
