from pathlib import Path

from take_home.causal_chains.agents.agents.causal_chain.causal_chain import causal_chain
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


def test_causal_chain_prompt_and_tools():
    prompt = (Path(__file__).parent / "prompts" / "causal_chain.md").read_text()
    assert causal_chain.instructions == prompt
    assert causal_chain.name == "causal_chain"
    assert causal_chain.model == "gpt-5.6-luna"
    assert causal_chain.output_type is Situation
    assert "# Goal" in prompt
    assert "# Iterative Process" in prompt
    assert "# Communication" in prompt
    assert (
        "Always write a short preamble before you call a tool. "
        "Say what you are about to do and why, then a blank line, "
        "so the reader sees it before the tool runs."
    ) in prompt
    assert "# Key Rules" not in prompt
    assert "# Examples" not in prompt
    for tool_name in (
        "now_scout",
        "path_builder",
        "pricer",
        "add_situation",
        "link_situations",
        "make_deeplink_widget",
    ):
        assert tool_name not in prompt
    assert [tool.name for tool in causal_chain.tools] == [
        "now_scout",
        "path_builder",
        "pricer",
        "add_situation",
        "link_situations",
        "make_deeplink_widget",
    ]
    assert causal_chain.tools[-1].name == "make_deeplink_widget"
