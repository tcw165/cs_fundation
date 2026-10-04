from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.models.causal_chains.situation import StartSituation


def test_now_scout_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "now_scout.md").read_text()
    assert now_scout.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "add_start_situation" not in prompt
    assert "The input gives the case and the future." in prompt
    assert "Write a short title for the present, much shorter than the description." in prompt
    assert "Include several drivers behind that present." in prompt
    assert (
        "The drivers from the start situation still left to change start as that same list."
        in prompt
    )
    assert "Use the case id from the input." in prompt
    assert "Do not invent a case id." in prompt
    assert now_scout.model == "gpt-5.6-luna"
    assert now_scout.model_settings.reasoning.effort == "medium"
    assert now_scout.output_type is StartSituation
    assert any(isinstance(tool, WebSearchTool) for tool in now_scout.tools)
    assert [tool.name for tool in now_scout.tools if not isinstance(tool, WebSearchTool)] == [
        "add_start_situation",
    ]
