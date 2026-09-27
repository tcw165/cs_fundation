from uuid import UUID

import pytest

from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    require_single_root,
)


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_situation_docstring_says_it_is_the_stored_row():
    assert Situation.__doc__ is not None
    assert "Neo4j" in Situation.__doc__
    assert "CausalChain" in Situation.__doc__


def test_situation_fields():
    situation = Situation(situation_id=NOW_ID, desc="Strait shut.", is_root=True)
    assert situation.is_root is True
    assert situation.desc == "Strait shut."


def test_second_root_rejected():
    situations = [
        Situation(situation_id=NOW_ID, desc="now", is_root=True),
        Situation(situation_id=DEAL_ID, desc="deal", is_root=True),
    ]
    with pytest.raises(ValueError, match="expected one root"):
        require_single_root(situations)
