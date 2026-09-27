from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def test_now_scout_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "now_scout.md").read_text()
    agent = now_scout(InMemoryChainEditor())
    assert agent.instructions == prompt
    assert agent.model == "gpt-5.6-luna"
    assert any(isinstance(tool, WebSearchTool) for tool in agent.tools)
    assert [tool.name for tool in agent.tools if not isinstance(tool, WebSearchTool)] == [
        "get_chain",
        "add_event",
    ]
    assert agent.output_type is ToolAck
