from pathlib import Path

from take_home.causal_chains.agents.agents.causal_chain.causal_chain import causal_chain  # pragma: allowlist secret
from take_home.causal_chains.agents.agents.chief_of_staff.chief_of_staff import (  # pragma: allowlist secret
    chief_of_staff,
)


def test_chief_of_staff_welcomes_and_hands_off_hypotheticals():
    prompt = (Path(__file__).parent / "prompts" / "chief_of_staff.md").read_text()
    assert chief_of_staff.instructions == prompt
    assert chief_of_staff.name == "chief_of_staff"
    assert chief_of_staff.model == "gpt-5.6-luna"
    assert chief_of_staff.output_type is str
    assert "# Goal" in prompt
    assert "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "You are the chief of staff." in prompt
    assert "Welcome them first." in prompt
    assert (
        "When they ask a hypothetical question, or they want to explore how the present "
        "could lead to a future, hand that question to the helper who connects now to "
        "the hypothetical future."
    ) in prompt
    assert "Do not build the chain yourself." in prompt
    assert "not exploring a causal chain" in prompt
    assert "Do not hand the turn off." in prompt
    assert chief_of_staff.tools == []
    assert len(chief_of_staff.handoffs) == 1
    causal_handoff = chief_of_staff.handoffs[0]
    assert causal_handoff.agent_name == causal_chain.name
    assert causal_handoff.tool_name == "transfer_to_causal_chain"
    assert "hypothetical question" in causal_handoff.tool_description
    assert "causal chain" in causal_handoff.tool_description
    assert "Do not build the chain yourself." in causal_handoff.tool_description
    for tool_name in (
        "causal_chain",
        "transfer_to_causal_chain",
        "now_scout",
        "path_builder",
        "add_case",
        "deeplinks_finder",
        "show_deeplink_widget",
    ):
        assert tool_name not in prompt
    assert [guardrail.name for guardrail in chief_of_staff.input_guardrails] == [
        "input_guardrail",
    ]
    assert chief_of_staff.input_guardrails[0].run_in_parallel is False
