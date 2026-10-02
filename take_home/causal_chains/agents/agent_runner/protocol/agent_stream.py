from collections.abc import AsyncIterator
from typing import Protocol

from take_home.causal_chains.agents.models.messaging.message import Message


class AgentStream(Protocol):
    def cancel(self) -> None:
        """Stop the in-flight run."""
        ...

    def __aiter__(self) -> AsyncIterator[Message]:
        ...
