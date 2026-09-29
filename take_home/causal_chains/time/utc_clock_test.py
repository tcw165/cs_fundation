from datetime import timezone

from take_home.causal_chains.time.protocol.protocol import Clock
from take_home.causal_chains.time.utc_clock import UtcClock


def test_utc_clock_now_is_utc():
    clock = UtcClock()
    assert isinstance(clock, Clock)
    moment = clock.now()
    assert moment.tzinfo is timezone.utc
    assert moment.tzname() == "UTC"
