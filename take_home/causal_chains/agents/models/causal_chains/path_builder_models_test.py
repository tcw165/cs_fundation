from uuid import UUID

import pytest
from agents import function_tool
from agents.agent_output import AgentOutputSchema
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderRequest,
    PathBuilderResult,
)
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
END_ID = UUID("33333333-3333-4333-8333-333333333333")


def _start() -> StartSituation:
    return StartSituation(
        situation_id=NOW_ID,
        version=1,
        title="Strait shut.",
        desc="Strait shut.",
        potential_drivers=["blockade"],
        remained_drivers=[],
    )


def _mid() -> Situation:
    return Situation(
        situation_id=DEAL_ID,
        version=1,
        title="Talks open.",
        desc="Talks open.",
        remained_drivers=[],
    )


def _terminal() -> TerminalSituation:
    return TerminalSituation(
        situation_id=END_ID,
        version=1,
        title="The strait opens.",
        desc="The strait opens.",
        original_ask="the strait opens",
        remained_drivers=[],
    )


def test_request_keeps_a_start_and_a_mid_situation():
    from_start = PathBuilderRequest(
        from_situation=_start(),
        terminal_situation=_terminal(),
        prompt="one variable: the blockade lifts",
    )
    assert isinstance(from_start.from_situation, StartSituation)
    assert from_start.from_situation.potential_drivers == ["blockade"]

    from_mid = PathBuilderRequest(
        from_situation=_mid(),
        terminal_situation=_terminal(),
        prompt="one variable: the deal is signed",
    )
    assert type(from_mid.from_situation) is Situation


def test_request_rejects_an_empty_prompt_and_the_same_id():
    with pytest.raises(ValidationError, match="prompt is empty"):
        PathBuilderRequest(
            from_situation=_start(),
            terminal_situation=_terminal(),
            prompt="  ",
        )

    terminal = _terminal()
    with pytest.raises(ValidationError, match="same situation"):
        PathBuilderRequest(
            from_situation=Situation(
                situation_id=terminal.situation_id,
                version=1,
                title="same id",
                desc="same id",
                            remained_drivers=[],
),
            terminal_situation=terminal,
            prompt="close",
        )


def test_result_is_one_mid_situation_or_none():
    empty = PathBuilderResult()
    assert empty.situation is None

    saved = PathBuilderResult(situation=_mid())
    assert type(saved.situation) is Situation
    assert saved.situation.desc == "Talks open."


def test_result_rejects_a_start_or_a_terminal():
    with pytest.raises(ValidationError):
        PathBuilderResult.model_validate(
            {
                "situation": {
                    "situation_id": str(NOW_ID),
                    "version": 1,
                    "desc": "now",
                    "potential_drivers": ["blockade"],
                }
            }
        )
    with pytest.raises(ValidationError):
        PathBuilderResult.model_validate(
            {
                "situation": {
                    "situation_id": str(END_ID),
                    "version": 1,
                    "desc": "the end",
                    "original_ask": "the ask",
                }
            }
        )


@function_tool
async def _test(req: PathBuilderRequest) -> PathBuilderResult:
    """Probe the schema the agent sees for one path-builder step."""
    del req
    return PathBuilderResult()


def _descriptions(schema: object) -> list[str]:
    found: list[str] = []
    if isinstance(schema, dict):
        description = schema.get("description")
        if isinstance(description, str):
            found.append(description)
        for value in schema.values():
            found.extend(_descriptions(value))
    elif isinstance(schema, list):
        for item in schema:
            found.extend(_descriptions(item))
    return found


def test_model_shape_with_description():
    request_text = "\n".join(_descriptions(_test.params_json_schema))
    assert "The current situation this step leaves." in request_text
    assert "The saved future this chain is moving toward." in request_text
    assert "The direction for this one step." in request_text
    assert "including each saved link" in request_text
    assert "the one driver to change." in request_text
    assert "remained_situation_quota" not in request_text

    result_text = "\n".join(
        _descriptions(AgentOutputSchema(PathBuilderResult).json_schema())
    )
    assert "The one saved mid-chain situation" in result_text
    assert "already linked from the current situation" in result_text
    assert "with one driver changed." in result_text
    assert "None means no new situation was saved" in result_text
    assert "is already linked to the terminal" in result_text
