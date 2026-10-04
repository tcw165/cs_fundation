from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
)

CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_causal_chain_keeps_one_start():
    start = Situation(
        situation_id=NOW_ID,
        version=1,
        created_timestamp=CREATED,
        kind="start",
        title="now",
        desc="now",
        remained_drivers=[],
    )
    deal = Situation(situation_id=DEAL_ID, version=1, created_timestamp=CREATED, kind="situation", title="deal", desc="deal", remained_drivers=[])
    chain = CausalChain(situations=[start, deal], links=[])
    assert chain.situations == [start, deal]
    assert type(chain.situations[0]) is Situation
    assert chain.links == []


def test_causal_chain_keeps_a_terminal():
    start = Situation(
        situation_id=NOW_ID,
        version=1,
        created_timestamp=CREATED,
        kind="start",
        title="now",
        desc="now",
        remained_drivers=[],
    )
    terminal = Situation(
        situation_id=DEAL_ID,
        version=1,
        created_timestamp=CREATED,
        kind="terminal",
        title="the end",
        desc="the end",
        remained_drivers=[],
    )
    chain = CausalChain(situations=[start, terminal], links=[])
    assert chain.situations[1].kind == "terminal"


def test_causal_chain_parses_the_start_before_a_plain_situation():
    chain = CausalChain.model_validate(
        {
            "situations": [
                {
                    "situation_id": str(NOW_ID),
                    "version": 1,
                    "created_timestamp": "2026-10-01T00:00:00+00:00",
                    "title": "now",
                    "desc": "now",
                    "kind": "start",
                    "remained_drivers": ["blockade"],
                },
                {
                    "situation_id": str(DEAL_ID),
                    "version": 1,
                    "created_timestamp": "2026-10-01T00:00:00+00:00",
                    "title": "the end",
                    "desc": "the end",
                    "kind": "terminal",
                    "remained_drivers": [],
                },
            ],
            "links": [],
        }
    )
    assert chain.situations[0].kind == "start"
    assert chain.situations[1].kind == "terminal"


def test_causal_chain_rejects_two_starts():
    situations = [
        Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
                    remained_drivers=[],
),
        Situation(
            situation_id=DEAL_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="deal",
            desc="deal",
                    remained_drivers=[],
),
    ]
    with pytest.raises(ValidationError, match="expected one start"):
        CausalChain(situations=situations, links=[])
