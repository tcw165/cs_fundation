from pathlib import Path

from agents import WebSearchTool

from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderResult,
)


def test_path_builder_prompt_model_and_search():
    prompt = (Path(__file__).parent / "prompts" / "path_builder.md").read_text()
    assert path_builder.instructions == prompt
    assert "# Goal" in prompt
    assert "# Key Rules" not in prompt
    assert "# Examples" in prompt
    assert "## Common shape" in prompt
    assert (
        "step 0:\n"
        "- Read the current situation, its remained drivers, and the terminal situation.\n"
        "- Search the web for more context on those remained drivers.\n\n"
        "step 1:\n"
        "- Pick one remained driver from the current situation, and say why that one. "
        "Change only one driver from the current situation's remained drivers.\n"
        "- Write a short title for that one mid-chain situation. Name that driver in the description.\n"
        "- Save the next situation with that driver removed from the remained drivers. "
        "Save once. The id is assigned when the situation is saved.\n"
        "- Do not save a start or the terminal. Do not return two.\n\n"
        "step 3:\n"
        "- Ask what a person could move. Price the link from the current situation to the next situation. "
        "The stored probability is the mean of those inputs. Do not set a probability.\n"
        "- Save the link from the current situation to the next situation. Save that link once.\n\n"
        "step N:\n"
        "- Return the saved next situation when it is not the terminal.\n"
    ) in prompt
    assert "add_situation" not in prompt
    assert "link_situations" not in prompt
    assert "pricer" not in prompt
    assert "case id" in prompt
    assert "one driver" in prompt
    assert "key-factor" not in prompt
    assert "Write a short title for that one mid-chain situation." in prompt
    assert (
        "Change only one driver from the current situation's remained drivers"
        in prompt
    )
    assert "Save the next situation with that driver removed from the remained drivers." in prompt
    assert "Name that driver in the description." in prompt
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
