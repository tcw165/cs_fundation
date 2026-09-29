from datetime import datetime, timezone
from typing import override

from take_home.causal_chains.time.protocol.protocol import Clock


class UtcClock(Clock):
    @override
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
