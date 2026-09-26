from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.crystal_ball.crystal_ball import crystal_ball


def test_crystal_ball_uses_three_sub_agents():
    prompt = (Path(__file__).parent / "prompts" / "crystal_ball.md").read_text()
    assert crystal_ball.instructions == prompt
    assert crystal_ball.model == "gpt-5.6-luna"
    assert [tool.name for tool in crystal_ball.tools] == ["now_scout", "path_builder", "pricer"]
    assert not any(isinstance(tool, WebSearchTool) for tool in crystal_ball.tools)
