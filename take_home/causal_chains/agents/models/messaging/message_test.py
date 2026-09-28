from take_home.causal_chains.agents.models.messaging.message import Message


def test_message_parses():
    message = Message(
        message_id="m_1",
        conversation_id="1",
        turn_id="t_1",
        role="user",
        text="hello",
    )
    assert message.text == "hello"
