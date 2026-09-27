from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def test_path_builder_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "path_builder.md").read_text()
    agent = path_builder(InMemoryChainEditor())
    assert agent.instructions == prompt
    assert agent.model == "gpt-5.6-luna"
    assert any(isinstance(tool, WebSearchTool) for tool in agent.tools)
    names = [tool.name for tool in agent.tools if not isinstance(tool, WebSearchTool)]
    assert names == ["get_chain", "get_event", "add_event", "add_link", "mark_destination"]
    assert agent.output_type is ToolAck
