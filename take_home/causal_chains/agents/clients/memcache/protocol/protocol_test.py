from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache


class _Buffer:
    def __init__(self) -> None:
        self._parts: list[str] = []

    def append(self, text: str) -> None:
        self._parts.append(text)

    def flush(self) -> str:
        text = "".join(self._parts)
        self._parts.clear()
        return text


def test_memcache_protocol_appends_then_flushes():
    buffer = _Buffer()
    assert isinstance(buffer, Memcache)
    buffer.append("a")
    buffer.append("b")
    assert buffer.flush() == "ab"
    assert buffer.flush() == ""
