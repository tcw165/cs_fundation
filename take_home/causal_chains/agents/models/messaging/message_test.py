from take_home.causal_chains.agents.models.messaging.message import (
    DeeplinkCardMessage,
    HeartbeatMessage,
    MarkdownMessage,
    Role,
    message_adapter,
)


def test_markdown_message_parses():
    message = MarkdownMessage(
        message_id="m_1",
        role=Role.user,
        text="hello",
    )
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert restored.text == "hello"


def test_deeplink_message_parses():
    message = DeeplinkCardMessage(
        message_id="m_2",
        role=Role.other,
        link="/chain/now/1?title=now",
    )
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert restored.link == "/chain/now/1?title=now"


def test_heartbeat_message_parses():
    message = HeartbeatMessage(message_id="m_3")
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert isinstance(restored, HeartbeatMessage)
    assert restored.role is Role.meta
    assert restored.type == "heartbeat"
