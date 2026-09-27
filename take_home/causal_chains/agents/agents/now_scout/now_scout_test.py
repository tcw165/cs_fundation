from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


def test_now_scout_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "now_scout.md").read_text()
    assert now_scout.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "add_situation" not in prompt
    assert now_scout.model == "gpt-5.6-luna"
    assert now_scout.output_type is Situation
    assert any(isinstance(tool, WebSearchTool) for tool in now_scout.tools)
    assert [tool.name for tool in now_scout.tools if not isinstance(tool, WebSearchTool)] == [
        "add_situation",
    ]
