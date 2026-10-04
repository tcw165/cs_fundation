from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
    require_single_start,
)

CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_situation_fields():
    situation = Situation(
        situation_id=NOW_ID,
        version=1,
        created_timestamp=CREATED,
        kind="situation",
        title="Strait shut.",
        desc="Strait shut.",
        remained_drivers=[],
    )
    assert situation.version == 1
    assert situation.title == "Strait shut."
    assert situation.desc == "Strait shut."
    properties = Situation.model_json_schema()["properties"]
    assert properties["title"]["description"] == "A short and readable description within 100 words."
    assert (
        properties["desc"]["description"]
        == "Detailed statements in this situation (much longer than title)."
    )
    assert (
        properties["remained_drivers"]["description"]
        == "Drivers from the start situation still left to change."
    )
    assert (
        properties["created_timestamp"]["description"]
        == "When this situation was saved."
    )
    assert properties["kind"]["description"] == "A mid-chain situation."


def test_situation_json_is_not_a_terminal_situation():
    payload = {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
    }
    with pytest.raises(ValidationError):
        TerminalSituation.model_validate(payload)


def test_situation_rejects_the_ask_field():
    payload = {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
        "original_ask": "the ask",
    }
    with pytest.raises(ValidationError):
        Situation.model_validate(payload)


def test_situation_rejects_potential_drivers():
    payload = {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
        "potential_drivers": ["blockade"],
    }
    with pytest.raises(ValidationError):
        Situation.model_validate(payload)


def test_start_situation_carries_the_drivers():
    start = StartSituation(
        situation_id=NOW_ID,
        version=1,
        created_timestamp=CREATED,
        kind="start",
        title="Strait shut.",
        desc="Strait shut.",
        remained_drivers=["blockade", "rejected deal"],
    )
    assert start.remained_drivers == ["blockade", "rejected deal"]
    assert start.kind == "start"
    assert isinstance(start, Situation)
    properties = StartSituation.model_json_schema()["properties"]
    assert properties["kind"]["description"] == "The saved present."


def test_terminal_situation_carries_the_ask():
    terminal = TerminalSituation(
        situation_id=DEAL_ID,
        version=1,
        created_timestamp=CREATED,
        kind="terminal",
        title="Republicans win the House while Democrats take the Senate.",
        desc="Republicans win the House while Democrats take the Senate.",
        original_ask="Republicans win the House but Democrats take the senate during the Midterm.",
        remained_drivers=[],
    )
    assert "Senate" in terminal.desc
    assert terminal.original_ask.endswith("Midterm.")
    assert not isinstance(terminal, StartSituation)


def test_path_return_is_a_list_or_one_terminal():
    adapter = TypeAdapter(list[Situation] | TerminalSituation)
    situations = adapter.validate_python(
        [
            {
                "situation_id": str(NOW_ID),
                "version": 1,
                "created_timestamp": "2026-10-01T00:00:00+00:00",
                "kind": "situation",
                "title": "now",
                "desc": "now",
                "remained_drivers": [],
            }
        ]
    )
    assert isinstance(situations, list)
    assert type(situations[0]) is Situation

    terminal = adapter.validate_python(
        {
            "situation_id": str(DEAL_ID),
            "version": 1,
            "created_timestamp": "2026-10-01T00:00:00+00:00",
            "kind": "terminal",
            "title": "the end",
            "desc": "the end",
            "remained_drivers": [],
            "original_ask": "the ask",
        }
    )
    assert isinstance(terminal, TerminalSituation)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            [
                {
                    "situation_id": str(DEAL_ID),
                    "version": 1,
                    "title": "the end",
                    "desc": "the end",
                    "original_ask": "the ask",
                }
            ]
        )


def test_second_start_rejected():
    situations = [
        StartSituation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
                    remained_drivers=[],
),
        StartSituation(
            situation_id=DEAL_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="deal",
            desc="deal",
                    remained_drivers=[],
),
    ]
    with pytest.raises(ValueError, match="expected one start"):
        require_single_start(situations)
