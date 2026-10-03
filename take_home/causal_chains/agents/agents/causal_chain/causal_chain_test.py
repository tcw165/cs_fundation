from pathlib import Path

from take_home.causal_chains.agents.agents.causal_chain.causal_chain import causal_chain
from take_home.causal_chains.agents.agents.deeplinks_finder.deeplinks_finder import (
    deeplinks_finder,
)


def test_causal_chain_prompt_and_tools():
    prompt = (Path(__file__).parent / "prompts" / "causal_chain.md").read_text()
    assert causal_chain.instructions == prompt
    assert causal_chain.name == "causal_chain"
    assert causal_chain.model == "gpt-5.6-luna"
    assert causal_chain.output_type is str
    assert "# Goal & Role" in prompt
    assert "You are a helper to connect now to the hypothetical future." in prompt
    assert "# Iterative Process" not in prompt
    assert "# Communication" in prompt
    assert "quota" not in prompt
    assert "The input tells you how many attempts you have." not in prompt
    assert (
        "Write the story of how the current situation evolves to the asked situation "
        "only after that path exists."
    ) in prompt
    assert "The direction starts with the case id, then the open line, then the one change." in prompt
    assert "Create a case." in prompt
    assert "Save the future on that same case." in prompt
    assert (
        "Write the future's description in your own words and include the current time."
        in prompt
    )
    terminal_tool = next(
        tool for tool in causal_chain.tools if tool.name == "add_terminal_situation"
    )
    assert (
        terminal_tool.params_json_schema["properties"]["desc"]["description"]
        == "What is true in the future, in your own words, including the current time."
    )
    assert "Do not write the story until the last step." in prompt
    assert "Do not write the story during this repeat." in prompt
    assert "the only answer is that story" in prompt
    assert (
        "If the message does not state a hypothetical future, answer in one message "
        "that you only imagine causal chains for hypothetical questions, then stop. "
        "Do not create a case. Do not call a tool. Do not describe any other ability."
    ) in prompt
    assert (
        "For a message that does not state a hypothetical future, that one message "
        "only says you imagine causal chains for hypothetical questions, and you stop."
    ) in prompt
    assert "A preamble is not an answer." in prompt
    assert (
        "Every message is one paragraph followed by `\\n\\n`. "
        "That includes a preamble, the final answer, and any other text."
    ) in prompt
    assert "msg 1" not in prompt
    assert "The story is one or more messages." in prompt
    assert (
        "Always write a short preamble before you call a tool. "
        "The preamble is one message: say what you are about to do and why, then `\\n\\n`, "
        "so the reader sees it before the tool runs."
    ) in prompt
    assert "# Key Rules" not in prompt
    assert "# Examples" in prompt
    before_examples, examples = prompt.split("# Examples", 1)
    assert "now-scout" not in before_examples
    assert "path-builder" not in before_examples
    assert "now-scout" in examples
    assert "path-builder" in examples
    assert (
        "step 3:\n"
        "- Emit a preamble: you are about to take one step from the current situation toward the future. "
        "This is not the answer.\n\n"
        "step 4:\n"
    ) in examples
    for tool_name in (
        "now_scout",
        "path_builder",
        "pricer",
        "add_case",
        "get_case",
        "add_situation",
        "add_start_situation",
        "add_terminal_situation",
        "lookup_leaf_situations",
        "lookup_chain_so_far",
        "reaches_terminal",
        "link_situations",
        "show_deeplink_widget",
        "deeplinks_finder",
    ):
        assert tool_name not in prompt
    assert [tool.name for tool in causal_chain.tools] == [
        "add_case",
        "get_case",
        "now_scout",
        "add_terminal_situation",
        "reaches_terminal",
        "lookup_chain_so_far",
        "path_builder",
        "deeplinks_finder",
        "show_deeplink_widget",
    ]
    path_builder_tool = next(
        tool for tool in causal_chain.tools if tool.name == "path_builder"
    )
    assert path_builder_tool.params_json_schema["properties"].keys() == {
        "from_situation",
        "terminal_situation",
        "prompt",
    }
    assert "situation quota" not in path_builder_tool.description
    assert "Take one step from the current situation toward the future" in (
        path_builder_tool.description
    )
    assert "Either link the current situation to the terminal" in (
        path_builder_tool.description
    )
    now_scout_tool = next(
        tool for tool in causal_chain.tools if tool.name == "now_scout"
    )
    assert "Find the present" in now_scout_tool.description
    assert "Pass that case and the future you were given." in now_scout_tool.description
    assert "It comes back saved as the start." in now_scout_tool.description
    assert now_scout_tool.params_json_schema["properties"].keys() == {"case", "future"}
    assert "Pass the case you created and the future you were given." in prompt
    assert "pricer" not in [tool.name for tool in causal_chain.tools]
    assert "link_situations" not in [tool.name for tool in causal_chain.tools]
    assert [tool.name for tool in causal_chain.tools[-2:]] == [
        "deeplinks_finder",
        "show_deeplink_widget",
    ]
    assert causal_chain.input_guardrails == []
    assert "# Widget" in prompt
    assert "Find the in-app destination for the case and the description." in prompt
    assert "route is `/chain/<case_id>`" in prompt
    assert (
        "step N:\n"
        "- Emit a deeplink card widget.\n"
        "- Only after the start connects to the terminal, write the story of how the current situation evolves to the asked situation. This is the answer.\n"
    ) in prompt
    finder = next(tool for tool in causal_chain.tools if tool.name == "deeplinks_finder")
    assert finder.params_json_schema["properties"].keys() == {"case", "destination_desc"}
    assert finder.description == _finder_sentences(deeplinks_finder.instructions)


def _finder_sentences(prompt: str) -> str:
    parts: list[str] = []
    for line in prompt.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("- "):
            text = text[2:]
        parts.append(text.replace("`", ""))
    return " ".join(parts)
