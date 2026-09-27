from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.discovered_situations import (
    DiscoveredSituations,
)
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder


def test_path_builder_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "path_builder.md").read_text()
    assert path_builder.instructions == prompt
    assert path_builder.model == "gpt-5.6-luna"
    assert path_builder.output_type is DiscoveredSituations
    assert any(isinstance(tool, WebSearchTool) for tool in path_builder.tools)
    assert [tool.name for tool in path_builder.tools if not isinstance(tool, WebSearchTool)] == [
        "add_situation",
        "link_situations",
    ]
