from typing import Protocol, runtime_checkable


@runtime_checkable
class Memcache(Protocol):
    def append(self, text: str) -> None: ...

    def flush(self) -> str: ...
