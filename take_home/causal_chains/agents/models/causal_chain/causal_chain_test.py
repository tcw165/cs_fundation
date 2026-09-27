from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chain.causal_link import CausalLink
from take_home.causal_chains.agents.models.causal_chain.depth_bounds import DepthBounds
from take_home.causal_chains.agents.models.causal_chain.event import Event
from take_home.causal_chains.agents.models.causal_chain.evidence import Evidence
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs

CAUSE_ID = UUID("11111111-1111-4111-8111-111111111111")
EFFECT_ID = UUID("22222222-2222-4222-8222-222222222222")
LINK_ID = UUID("33333333-3333-4333-8333-333333333333")


def test_model_docstrings_name_the_invariant():
    for model in (Evidence, LinkInputs, DepthBounds, Event, CausalLink, CausalChain):
        assert model.__doc__ is not None
        assert len(model.__doc__.strip()) > 40


def test_log_odds_clamp_to_two():
    evidence = Evidence(note="shock", log_odds=Decimal("3"))
    assert evidence.log_odds == Decimal("2")
    evidence = Evidence(note="shock", log_odds=Decimal("-9"))
    assert evidence.log_odds == Decimal("-2")


def test_base_rate_zero_or_one_rejected():
    with pytest.raises(ValidationError):
        LinkInputs(base_rate=Decimal("0"), evidence=[])
    with pytest.raises(ValidationError):
        LinkInputs(base_rate=Decimal("1"), evidence=[])


def test_root_depth_must_be_zero():
    with pytest.raises(ValidationError, match="root depth is 0"):
        Event(
            event_id=CAUSE_ID,
            statement="now",
            depth=1,
            is_root=True,
        )


def test_chain_starts_empty():
    chain = CausalChain()
    assert chain.root_id is None
    assert chain.events == {}
    assert chain.links == {}
    assert chain.depth_bounds.min_depth == 2
    assert chain.depth_bounds.max_depth == 4
    assert chain.max_children == 4


def test_self_edge_rejected():
    with pytest.raises(ValidationError, match="self-edge"):
        CausalLink(link_id=LINK_ID, cause_id=CAUSE_ID, effect_id=CAUSE_ID)
