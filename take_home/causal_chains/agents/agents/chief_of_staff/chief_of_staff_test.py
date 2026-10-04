from datetime import datetime, timezone
from pathlib import Path

from take_home.causal_chains.agents.agents.causal_chain.causal_chain import causal_chain  # pragma: allowlist secret
from take_home.causal_chains.agents.agents.chief_of_staff.chief_of_staff import (  # pragma: allowlist secret
    build_chief_of_staff,
)


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 9, 30, tzinfo=timezone.utc)


class _Store:
    async def search_messages(
        self,
        conversation_id: str,
        since: datetime,
        until: datetime,
    ) -> list[object]:
        return []


def test_chief_of_staff_hands_off_the_latest_future():
    prompt = (Path(__file__).parent / "prompts" / "chief_of_staff.md").read_text()
    chief_of_staff = build_chief_of_staff(
        conversation_id="1",
        messaging_store=_Store(),
        clock=_Clock(),
    )
    assert chief_of_staff.instructions == prompt
    assert chief_of_staff.name == "chief_of_staff"
    assert chief_of_staff.model == "gpt-5.6-luna"
    assert chief_of_staff.model_settings.reasoning.effort == "medium"
    assert chief_of_staff.output_type is str
    assert prompt.startswith("# Role & Goal\n")
    assert "# Key Rules" in prompt
    assert "# Communication Primitive" in prompt
    assert "# Examples" not in prompt
    assert "You are the chief of staff." in prompt
    assert "The latest user message is the question." in prompt
    assert "If it is still not there, ask them to clarify." in prompt
    assert "Welcome only when that question is not a hypothetical." in prompt
    assert "Welcome them first." not in prompt
    assert "hand it off as written" in prompt
    assert "Do not ask them to confirm or rephrase." in prompt
    assert "Do not build the chain yourself." in prompt
    assert "not exploring a causal chain" in prompt
    assert "Do not hand the turn off." in prompt
    assert [tool.name for tool in chief_of_staff.tools] == [
        "search_conversation_messages",
    ]
    assert len(chief_of_staff.handoffs) == 1
    causal_handoff = chief_of_staff.handoffs[0]
    assert causal_handoff.agent_name == causal_chain.name
    assert causal_handoff.tool_name == "transfer_to_causal_chain"
    assert "future change" in causal_handoff.tool_description
    assert "as written" in causal_handoff.tool_description
    assert "Do not build the chain yourself." in causal_handoff.tool_description
    for tool_name in (
        "causal_chain",
        "transfer_to_causal_chain",
        "search_messages",
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
