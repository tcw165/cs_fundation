from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


def test_path_builder_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "path_builder.md").read_text()
    assert path_builder.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "states that same claim" in prompt
    assert "add_situation" not in prompt
    assert "link_situations" not in prompt
    assert path_builder.model == "gpt-5.6-luna"
    assert path_builder.output_type == list[Situation]
    assert any(isinstance(tool, WebSearchTool) for tool in path_builder.tools)
    assert [tool.name for tool in path_builder.tools if not isinstance(tool, WebSearchTool)] == [
        "add_situation",
    ]
