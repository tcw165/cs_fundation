from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def test_pricer_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "pricer.md").read_text()
    agent = pricer(InMemoryChainEditor())
    assert agent.instructions == prompt
    assert agent.model == "gpt-5.6-luna"
    assert any(isinstance(tool, WebSearchTool) for tool in agent.tools)
    names = [tool.name for tool in agent.tools if not isinstance(tool, WebSearchTool)]
    assert names == ["get_chain", "list_effects", "set_link_inputs"]
    assert agent.output_type is ToolAck
