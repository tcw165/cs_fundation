import pytest

from take_home.causal_chains.agents.constants.headers import MessagingConstants


def test_short_poll_interval_is_one_second():
    assert MessagingConstants.SHORT_POLL_INTERVAL_MS == 1000
    assert MessagingConstants.SHORT_POLL_INTERVAL_HEADER == "x-short-poll-interval-ms"


def test_messaging_constants_are_frozen():
    with pytest.raises(TypeError, match="frozen"):
        MessagingConstants.SHORT_POLL_INTERVAL_MS = 5
    with pytest.raises(TypeError, match="frozen"):
        MessagingConstants.SHORT_POLL_INTERVAL_HEADER = "x-other"
