from take_home.causal_chains.agents.observability.logging import (
    bind_conversation_logger,
    bind_logger,
    bind_session_logger,
    logger,
)


def test_logger_is_unbound_until_a_session_is_bound():
    unbound = logger()
    assert unbound.extra == {}
    assert unbound.logger.name == "agents"


def test_bind_session_logger_sets_extra_and_resets():
    with bind_session_logger("c_1", "t_1") as bound:
        assert bound.extra == {"conversation_id": "c_1", "turn_id": "t_1"}
        assert logger() is bound
    assert logger().extra == {}


def test_bind_conversation_logger_sets_conversation_and_resets():
    with bind_conversation_logger("c_1") as bound:
        assert bound.extra == {"conversation_id": "c_1", "turn_id": ""}
        assert logger() is bound
    assert logger().extra == {}


def test_bind_logger_sets_empty_ids_and_resets():
    with bind_logger() as bound:
        assert bound.extra == {}
        assert logger() is bound
    assert logger().extra == {}
