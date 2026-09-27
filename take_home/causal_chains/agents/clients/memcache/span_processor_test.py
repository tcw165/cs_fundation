import json
from types import SimpleNamespace

from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.clients.memcache.span_processor import MemcacheSpanProcessor


def test_on_span_end_appends_exported_span():
    cache = InMemoryMemcache()
    processor = MemcacheSpanProcessor(cache)
    processor.on_span_end(SimpleNamespace(export=lambda: {"name": "now_scout"}))
    assert cache.flush() == json.dumps({"name": "now_scout"}) + "\n"


def test_on_span_end_skips_missing_export():
    cache = InMemoryMemcache()
    processor = MemcacheSpanProcessor(cache)
    processor.on_span_end(SimpleNamespace(export=lambda: None))
    assert cache.flush() == ""
