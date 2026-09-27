from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache


def test_in_memory_memcache_appends_then_flushes():
    cache = InMemoryMemcache()
    assert isinstance(cache, Memcache)
    cache.append("a")
    cache.append("b")
    assert cache.flush() == "ab"
    assert cache.flush() == ""
