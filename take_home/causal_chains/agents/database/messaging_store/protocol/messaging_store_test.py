from take_home.causal_chains.models.message import Message


def test_message_fields_for_store():
    message = Message(
        message_id="m_1",
        conversation_id="1",
        turn_id="t_1",
        role="user",
        text="hello",
    )
    assert message.conversation_id == "1"
    assert message.role == "user"
    assert message.text == "hello"
