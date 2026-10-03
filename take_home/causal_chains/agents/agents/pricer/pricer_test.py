from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.models.causal_chains.link_inputs import LinkInputs


def test_pricer_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "pricer.md").read_text()
    assert pricer.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "Search the web" in prompt
    assert "link_situations" not in prompt
    assert pricer.model == "gpt-5.6-luna"
    assert pricer.model_settings.reasoning.effort == "medium"
    assert pricer.output_type is LinkInputs
    assert any(isinstance(tool, WebSearchTool) for tool in pricer.tools)
