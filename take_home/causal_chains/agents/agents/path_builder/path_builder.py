from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.chain_editor.protocol.protocol import ChainEditor
from take_home.causal_chains.agents.chain_editor.sdk_tools import sdk_tools
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


def path_builder(editor: ChainEditor) -> Agent[RunContext]:
    """Add events and links on this editor. Do not set probabilities."""
    return Agent[RunContext](
        name="path_builder",
        instructions=_read_prompt("path_builder.md"),
        model="gpt-5.6-luna",
        tools=[
            WebSearchTool(),
            *sdk_tools(
                editor,
                ("get_chain", "get_event", "add_event", "add_link", "mark_destination"),
            ),
        ],
        output_type=ToolAck,
    )
