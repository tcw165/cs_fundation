from decimal import Decimal
from pathlib import Path

from take_home.causal_chains.agents.agents.crystal_ball.examine import examine
from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs


def _price(editor: InMemoryChainEditor) -> None:
    for link in list(editor.get_chain().links.values()):
        editor.set_link_inputs(
            link.link_id,
            LinkInputs(base_rate=Decimal("0.50"), evidence=[]),
        )


def _hormuz() -> CausalChain:
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    deal = editor.add_event("deal", root.event_id)
    no_deal = editor.add_event("no deal", root.event_id)
    clear = editor.add_event("clear", deal.event_id)
    stuck = editor.add_event("stuck", deal.event_id)
    resumes = editor.add_event("resumes", no_deal.event_id)
    shut = editor.add_event("shut", no_deal.event_id)
    editor.add_link(root.event_id, deal.event_id)
    editor.add_link(root.event_id, no_deal.event_id)
    editor.add_link(deal.event_id, clear.event_id)
    editor.add_link(deal.event_id, stuck.event_id)
    editor.add_link(no_deal.event_id, resumes.event_id)
    editor.add_link(no_deal.event_id, shut.event_id)
    editor.mark_destination(clear.event_id)
    editor.mark_destination(resumes.event_id)
    _price(editor)
    return editor.get_chain()


def test_hormuz_scores_five():
    exam = examine(_hormuz())
    assert exam.score == 5
    assert exam.failures == []


def test_three_children_can_all_be_destinations():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    left = editor.add_event("left", root.event_id)
    right = editor.add_event("right", root.event_id)
    editor.add_link(root.event_id, left.event_id)
    editor.add_link(root.event_id, right.event_id)
    for name in ("cut", "hold", "hike"):
        child = editor.add_event(name, left.event_id)
        editor.add_link(left.event_id, child.event_id)
        editor.mark_destination(child.event_id)
    for name in ("rally", "fade"):
        child = editor.add_event(name, right.event_id)
        editor.add_link(right.event_id, child.event_id)
        editor.mark_destination(child.event_id)
    _price(editor)
    exam = examine(editor.get_chain())
    assert exam.score == 5
    assert exam.failures == []


def test_outgoing_sum_failure():
    chain = _hormuz()
    first = next(iter(chain.links.values()))
    first.p = Decimal("0.10")
    exam = examine(chain)
    assert "outgoing probabilities do not sum to 1" in exam.failures
    assert exam.score == 4


def test_skill_names_the_loop():
    skill = (Path(__file__).parents[3] / ".agents" / "hill-climb" / "SKILL.md").read_text()
    assert "The Strait of Hormuz is going to open next week." in skill
    assert "examine" in skill
    assert "one change" in skill
    assert "score does not rise" in skill
