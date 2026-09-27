from decimal import Decimal

import pytest

from take_home.causal_chains.agents.chain_editor.in_memory_chain_editor import (
    InMemoryChainEditor,
)
from take_home.causal_chains.agents.chain_editor.protocol.protocol import ChainEditor
from take_home.causal_chains.agents.models.causal_chain.evidence import Evidence
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs


def _inputs(base_rate: str, log_odds: str | None = None) -> LinkInputs:
    evidence = []
    if log_odds is not None:
        evidence.append(Evidence(note="note", log_odds=Decimal(log_odds)))
    return LinkInputs(base_rate=Decimal(base_rate), evidence=evidence)


def test_editor_satisfies_the_protocol():
    assert isinstance(InMemoryChainEditor(), ChainEditor)


def test_three_children_normalize_to_one():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    effects = [editor.add_event(f"path {index}", root.event_id) for index in range(3)]
    links = [editor.add_link(root.event_id, effect.event_id) for effect in effects]
    for link in links:
        editor.set_link_inputs(link.link_id, _inputs("0.20"))
    shares = [editor.get_chain().links[link.link_id].p for link in links]
    assert all(share is not None for share in shares)
    assert sum(shares, Decimal("0")) == Decimal("1.000000")
    assert shares[0] != Decimal("0.20")


def test_p_stays_unset_until_every_sibling_has_inputs():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    first = editor.add_event("cut", root.event_id)
    second = editor.add_event("hold", root.event_id)
    first_link = editor.add_link(root.event_id, first.event_id)
    editor.add_link(root.event_id, second.event_id)
    priced = editor.set_link_inputs(first_link.link_id, _inputs("0.40"))
    assert priced.raw_p is not None
    assert priced.p is None


def test_fifth_child_rejected():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    for index in range(4):
        effect = editor.add_event(f"path {index}", root.event_id)
        editor.add_link(root.event_id, effect.event_id)
    extra = editor.add_event("path 4", root.event_id)
    with pytest.raises(ValueError, match="max_children"):
        editor.add_link(root.event_id, extra.event_id)


def test_depth_past_max_rejected():
    editor = InMemoryChainEditor()
    current = editor.add_event("now")
    for depth in range(1, 5):
        current = editor.add_event(f"depth {depth}", current.event_id)
    assert current.depth == 4
    with pytest.raises(ValueError, match="depth is past max_depth"):
        editor.add_event("too deep", current.event_id)


def test_skip_edge_rejected():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    mid = editor.add_event("mid", root.event_id)
    leaf = editor.add_event("leaf", mid.event_id)
    with pytest.raises(ValueError, match="skip edge"):
        editor.add_link(root.event_id, leaf.event_id)


def test_set_event_stales_descendants_only():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    mid = editor.add_event("cut 25bp", root.event_id)
    leaf = editor.add_event("rally", mid.event_id)
    other = editor.add_event("hold", root.event_id)
    incoming = editor.add_link(root.event_id, mid.event_id)
    downstream = editor.add_link(mid.event_id, leaf.event_id)
    side = editor.add_link(root.event_id, other.event_id)
    for link in (incoming, downstream, side):
        editor.set_link_inputs(link.link_id, _inputs("0.50"))
    editor.set_event(mid.event_id, "cut 50bp")
    chain = editor.get_chain()
    assert chain.links[incoming.link_id].stale is False
    assert chain.links[incoming.link_id].p is not None
    assert chain.links[downstream.link_id].stale is True
    assert chain.links[downstream.link_id].p is None
    assert chain.links[side.link_id].stale is False
    assert chain.events[mid.event_id].statement == "cut 50bp"


def test_p_query_uses_depth_bounds():
    editor = InMemoryChainEditor()
    root = editor.add_event("now")
    deal = editor.add_event("deal", root.event_id)
    no_deal = editor.add_event("no deal", root.event_id)
    clear = editor.add_event("clear", deal.event_id)
    shut = editor.add_event("shut", no_deal.event_id)
    deal_link = editor.add_link(root.event_id, deal.event_id)
    no_deal_link = editor.add_link(root.event_id, no_deal.event_id)
    clear_link = editor.add_link(deal.event_id, clear.event_id)
    shut_link = editor.add_link(no_deal.event_id, shut.event_id)
    editor.set_link_inputs(deal_link.link_id, _inputs("0.25"))
    editor.set_link_inputs(no_deal_link.link_id, _inputs("0.75"))
    editor.set_link_inputs(clear_link.link_id, _inputs("0.50"))
    editor.set_link_inputs(shut_link.link_id, _inputs("0.50"))
    editor.mark_destination(clear.event_id)
    assert editor.p_query() == Decimal("0.250000")
    shallow = InMemoryChainEditor()
    shallow_root = shallow.add_event("now")
    yes = shallow.add_event("yes", shallow_root.event_id)
    only = shallow.add_link(shallow_root.event_id, yes.event_id)
    shallow.set_link_inputs(only.link_id, _inputs("0.40"))
    shallow.mark_destination(yes.event_id)
    assert yes.depth == 1
    assert shallow.p_query() == Decimal("0")


def test_second_root_rejected():
    editor = InMemoryChainEditor()
    editor.add_event("now")
    with pytest.raises(ValueError, match="root already exists"):
        editor.add_event("also now")
