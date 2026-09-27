from pathlib import Path

from agents import Agent

from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.chain_editor.protocol.protocol import ChainEditor
from take_home.causal_chains.agents.chain_editor.sdk_tools import sdk_tools
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


def crystal_ball(editor: ChainEditor) -> Agent[RunContext]:
    """Host agent. Sub-agents share this editor. This agent only reads the chain."""
    return Agent[RunContext](
        name="crystal_ball",
        instructions=_read_prompt("crystal_ball.md"),
        model="gpt-5.6-luna",
        tools=[
            now_scout(editor).as_tool(
                tool_name="now_scout",
                tool_description="Write the root event from the live present.",
            ),
            path_builder(editor).as_tool(
                tool_name="path_builder",
                tool_description="Add the events and links from that root to the query.",
            ),
            pricer(editor).as_tool(
                tool_name="pricer",
                tool_description="Set inputs on every link. Code derives p.",
            ),
            *sdk_tools(editor, ("get_chain",)),
        ],
        output_type=ToolAck,
    )
