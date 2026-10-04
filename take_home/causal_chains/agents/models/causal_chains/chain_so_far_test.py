from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.chain_so_far import (
    ChainSoFar,
    LinkedHop,
)
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
NEXT_ID = UUID("44444444-4444-4444-8444-444444444444")
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


def _mid(situation_id: UUID = DEAL_ID, desc: str = "Talks open.") -> Situation:
    return Situation(
        situation_id=situation_id,
        version=1,
        title=desc,
        desc=desc,
        remained_drivers=[],
    )


def _link(from_situation: Situation, to_situation: Situation) -> LeadsTo:
    return LeadsTo(
        from_situation_id=from_situation.situation_id,
        from_version=from_situation.version,
        to_situation_id=to_situation.situation_id,
        to_version=to_situation.version,
        p=Decimal("0.5"),
    )


def test_chain_so_far_is_the_start_when_nothing_is_linked():
    line = ChainSoFar(start=_start())
    assert line.hops == []


def test_chain_so_far_keeps_hops_that_follow_the_line():
    start = _start()
    mid = _mid()
    later = _mid(NEXT_ID, "The deal is signed.")
    line = ChainSoFar(
        start=start,
        hops=[
            LinkedHop(situation=mid, link=_link(start, mid)),
            LinkedHop(situation=later, link=_link(mid, later)),
        ],
    )
    assert [hop.situation.situation_id for hop in line.hops] == [DEAL_ID, NEXT_ID]


def test_chain_so_far_rejects_a_hop_that_does_not_follow():
    start = _start()
    mid = _mid()
    other = _mid(NEXT_ID, "Somewhere else.")
    with pytest.raises(ValidationError, match="does not follow"):
        ChainSoFar(
            start=start,
            hops=[LinkedHop(situation=mid, link=_link(other, mid))],
        )
    with pytest.raises(ValidationError, match="does not follow"):
        ChainSoFar(
            start=start,
            hops=[LinkedHop(situation=other, link=_link(start, mid))],
        )


def test_chain_so_far_rejects_a_start_or_a_terminal_hop():
    start = _start()
    terminal = TerminalSituation(
        situation_id=END_ID,
        version=1,
        title="The strait opens.",
        desc="The strait opens.",
        original_ask="the strait opens",
        remained_drivers=[],
    )
    with pytest.raises(ValidationError, match="mid-chain"):
        ChainSoFar(
            start=start,
            hops=[LinkedHop(situation=start, link=_link(start, _mid()))],
        )
    with pytest.raises(ValidationError, match="mid-chain"):
        ChainSoFar(
            start=start,
            hops=[LinkedHop(situation=terminal, link=_link(start, terminal))],
        )
