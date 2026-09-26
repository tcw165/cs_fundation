from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout


def test_now_scout_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "now_scout.md").read_text()
    assert now_scout.instructions == prompt
    assert now_scout.model == "gpt-5.6-luna"
    assert any(isinstance(tool, WebSearchTool) for tool in now_scout.tools)
