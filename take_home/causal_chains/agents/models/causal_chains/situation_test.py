from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    TerminalSituation,
    require_single_root,
)


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_situation_fields():
    situation = Situation(
        situation_id=NOW_ID,
        version=1,
        desc="Strait shut.",
        is_root=True,
    )
    assert situation.version == 1
    assert situation.is_root is True
    assert situation.desc == "Strait shut."


def test_situation_json_is_not_a_terminal_situation():
    payload = {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
        "is_root": True,
    }
    with pytest.raises(ValidationError):
        TerminalSituation.model_validate(payload)


def test_situation_rejects_the_ask_field():
    payload = {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
        "is_root": True,
        "original_ask": "the ask",
    }
    with pytest.raises(ValidationError):
        Situation.model_validate(payload)


def test_terminal_situation_carries_the_ask():
    terminal = TerminalSituation(
        situation_id=DEAL_ID,
        version=1,
        desc="Republicans win the House while Democrats take the Senate.",
        is_root=False,
        original_ask="Republicans win the House but Democrats take the senate during the Midterm.",
    )
    assert terminal.is_root is False
    assert "Senate" in terminal.desc
    assert terminal.original_ask.endswith("Midterm.")


def test_path_return_is_a_list_or_one_terminal():
    adapter = TypeAdapter(list[Situation] | TerminalSituation)
    situations = adapter.validate_python(
        [
            {
                "situation_id": str(NOW_ID),
                "version": 1,
                "desc": "now",
                "is_root": False,
            }
        ]
    )
    assert isinstance(situations, list)
    assert type(situations[0]) is Situation

    terminal = adapter.validate_python(
        {
            "situation_id": str(DEAL_ID),
            "version": 1,
            "desc": "the end",
            "is_root": False,
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
                    "desc": "the end",
                    "is_root": False,
                    "original_ask": "the ask",
                }
            ]
        )


def test_second_root_rejected():
    situations = [
        Situation(situation_id=NOW_ID, version=1, desc="now", is_root=True),
        Situation(situation_id=DEAL_ID, version=1, desc="deal", is_root=True),
    ]
    with pytest.raises(ValueError, match="expected one root"):
        require_single_root(situations)
