from decimal import Decimal
from pathlib import Path
from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.chain_graph import ChainGraph
from take_home.causal_chains.agents.agents.crystal_ball.examine import examine
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
NO_DEAL_ID = UUID("33333333-3333-4333-8333-333333333333")
CLEAR_ID = UUID("44444444-4444-4444-8444-444444444444")
STUCK_ID = UUID("55555555-5555-4555-8555-555555555555")
RESUMES_ID = UUID("66666666-6666-4666-8666-666666666666")
SHUT_ID = UUID("77777777-7777-4777-8777-777777777777")


def _hormuz() -> ChainGraph:
    return ChainGraph(
        situations=[
            Situation(situation_id=NOW_ID, desc="now", is_root=True),
            Situation(situation_id=DEAL_ID, desc="deal", is_root=False),
            Situation(situation_id=NO_DEAL_ID, desc="no deal", is_root=False),
            Situation(situation_id=CLEAR_ID, desc="clear", is_root=False),
            Situation(situation_id=STUCK_ID, desc="stuck", is_root=False),
            Situation(situation_id=RESUMES_ID, desc="resumes", is_root=False),
            Situation(situation_id=SHUT_ID, desc="shut", is_root=False),
        ],
        edges=[
            LeadsTo(from_situation_id=NOW_ID, to_situation_id=DEAL_ID, p=Decimal("0.08")),
            LeadsTo(from_situation_id=NOW_ID, to_situation_id=NO_DEAL_ID, p=Decimal("0.92")),
            LeadsTo(from_situation_id=DEAL_ID, to_situation_id=CLEAR_ID, p=Decimal("0.20")),
            LeadsTo(from_situation_id=DEAL_ID, to_situation_id=STUCK_ID, p=Decimal("0.80")),
            LeadsTo(from_situation_id=NO_DEAL_ID, to_situation_id=RESUMES_ID, p=Decimal("0.005")),
            LeadsTo(from_situation_id=NO_DEAL_ID, to_situation_id=SHUT_ID, p=Decimal("0.995")),
        ],
        destination_ids=[CLEAR_ID, RESUMES_ID],
    )


def test_hormuz_scores_five():
    exam = examine(_hormuz())
    assert exam.score == 5
    assert exam.failures == []


def test_outgoing_sum_failure():
    graph = _hormuz()
    graph.edges[3] = LeadsTo(from_situation_id=DEAL_ID, to_situation_id=STUCK_ID, p=Decimal("0.70"))
    exam = examine(graph)
    assert "outgoing probabilities do not sum to 1" in exam.failures
    assert exam.score == 4


def test_skill_names_the_loop():
    skill = (
        Path(__file__).parents[3] / ".agents" / "hill-climb" / "SKILL.md"
    ).read_text()
    assert "The Strait of Hormuz is going to open next week." in skill
    assert "examine" in skill
    assert "one change" in skill
    assert "score does not rise" in skill
