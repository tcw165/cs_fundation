from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_causal_chain_keeps_one_root():
    root = Situation(situation_id=NOW_ID, version=1, desc="now", is_root=True)
    deal = Situation(situation_id=DEAL_ID, version=1, desc="deal", is_root=False)
    chain = CausalChain(situations=[root, deal], links=[])
    assert chain.situations == [root, deal]
    assert chain.links == []


def test_causal_chain_rejects_two_roots():
    situations = [
        Situation(situation_id=NOW_ID, version=1, desc="now", is_root=True),
        Situation(situation_id=DEAL_ID, version=1, desc="deal", is_root=True),
    ]
    with pytest.raises(ValidationError, match="expected one root"):
        CausalChain(situations=situations, links=[])
