from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)


def test_each_status_value_is_its_name():
    for status in ConversationStatus:
        assert status.value == status.name
