from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_causal_chain_keeps_one_start():
    start = StartSituation(
        situation_id=NOW_ID,
        version=1,
        title="now",
        desc="now",
        potential_drivers=["blockade"],
    )
    deal = Situation(situation_id=DEAL_ID, version=1, title="deal", desc="deal")
    chain = CausalChain(situations=[start, deal], links=[])
    assert chain.situations == [start, deal]
    assert type(chain.situations[0]) is StartSituation
    assert chain.links == []


def test_causal_chain_keeps_a_terminal():
    start = StartSituation(
        situation_id=NOW_ID,
        version=1,
        title="now",
        desc="now",
        potential_drivers=["blockade"],
    )
    terminal = TerminalSituation(
        situation_id=DEAL_ID,
        version=1,
        title="the end",
        desc="the end",
        original_ask="the ask",
    )
    chain = CausalChain(situations=[start, terminal], links=[])
    assert type(chain.situations[1]) is TerminalSituation
    assert chain.situations[1].original_ask == "the ask"


def test_causal_chain_parses_the_start_before_a_plain_situation():
    chain = CausalChain.model_validate(
        {
            "situations": [
                {
                    "situation_id": str(NOW_ID),
                    "version": 1,
                    "title": "now",
                    "desc": "now",
                    "potential_drivers": ["blockade"],
                },
                {
                    "situation_id": str(DEAL_ID),
                    "version": 1,
                    "title": "the end",
                    "desc": "the end",
                    "original_ask": "the ask",
                },
            ],
            "links": [],
        }
    )
    assert type(chain.situations[0]) is StartSituation
    assert type(chain.situations[1]) is TerminalSituation


def test_causal_chain_rejects_two_starts():
    situations = [
        StartSituation(
            situation_id=NOW_ID,
            version=1,
            title="now",
            desc="now",
            potential_drivers=["blockade"],
        ),
        StartSituation(
            situation_id=DEAL_ID,
            version=1,
            title="deal",
            desc="deal",
            potential_drivers=["talks"],
        ),
    ]
    with pytest.raises(ValidationError, match="expected one start"):
        CausalChain(situations=situations, links=[])
