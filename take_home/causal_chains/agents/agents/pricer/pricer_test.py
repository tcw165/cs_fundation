from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.pricer.pricer import pricer


def test_pricer_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "pricer.md").read_text()
    assert pricer.instructions == prompt
    assert pricer.model == "gpt-5.6-luna"
    assert any(isinstance(tool, WebSearchTool) for tool in pricer.tools)
