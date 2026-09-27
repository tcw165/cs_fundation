from typing import override

from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache


class InMemoryMemcache(Memcache):
    def __init__(self) -> None:
        self._parts: list[str] = []

    @override
    def append(self, text: str) -> None:
        self._parts.append(text)

    @override
    def flush(self) -> str:
        text = "".join(self._parts)
        self._parts.clear()
        return text
