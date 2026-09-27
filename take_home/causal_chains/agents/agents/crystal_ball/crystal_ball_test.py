from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.crystal_ball.crystal_ball import crystal_ball
from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.models.tool_ack import ToolAck


def test_crystal_ball_uses_three_sub_agents():
    prompt = (Path(__file__).parent / "prompts" / "crystal_ball.md").read_text()
    agent = crystal_ball(InMemoryChainEditor())
    assert agent.instructions == prompt
    assert agent.model == "gpt-5.6-luna"
    assert [tool.name for tool in agent.tools] == [
        "now_scout",
        "path_builder",
        "pricer",
        "get_chain",
    ]
    assert not any(isinstance(tool, WebSearchTool) for tool in agent.tools)
    assert agent.output_type is ToolAck
