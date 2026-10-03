from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderResult,
)


def test_path_builder_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "path_builder.md").read_text()
    assert path_builder.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "add_situation" not in prompt
    assert "link_situations" not in prompt
    assert "pricer" not in prompt
    assert "case id" in prompt
    assert "one key-factor" in prompt
    assert "Save that link once the step is sorted out." in prompt
    assert "including each saved link" in prompt
    assert "remained_situation_quota" not in prompt
    assert "no room remains" not in prompt
    assert "When the one remaining change is the terminal itself" in prompt
    assert "Return no situation" in prompt
    assert "mean of those inputs" in prompt
    assert path_builder.model == "gpt-5.6-luna"
    assert path_builder.model_settings.reasoning.effort == "medium"
    assert path_builder.output_type is PathBuilderResult
    assert any(isinstance(tool, WebSearchTool) for tool in path_builder.tools)
    assert [tool.name for tool in path_builder.tools if not isinstance(tool, WebSearchTool)] == [
        "add_situation",
        "pricer",
        "link_situations",
    ]
