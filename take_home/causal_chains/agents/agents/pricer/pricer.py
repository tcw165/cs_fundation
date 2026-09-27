from pathlib import Path

from agents import Agent, WebSearchTool

from take_home.causal_chains.agents.chain_editor.protocol.protocol import ChainEditor
from take_home.causal_chains.agents.chain_editor.sdk_tools import sdk_tools
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


def pricer(editor: ChainEditor) -> Agent[RunContext]:
    """Fill link inputs on this editor. Code derives p."""
    return Agent[RunContext](
        name="pricer",
        instructions=_read_prompt("pricer.md"),
        model="gpt-5.6-luna",
        tools=[
            WebSearchTool(),
            *sdk_tools(editor, ("get_chain", "list_effects", "set_link_inputs")),
        ],
        output_type=ToolAck,
    )
