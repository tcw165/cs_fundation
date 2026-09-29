from datetime import datetime, timezone

from take_home.causal_chains.time.protocol.protocol import Clock


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


def test_clock_protocol_returns_a_moment():
    clock = _FixedClock()
    assert isinstance(clock, Clock)
    moment = clock.now()
    assert moment == datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)
    assert moment.tzinfo is not None
