from datetime import datetime, timezone

from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Role,
    message_adapter,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)


def test_markdown_message_parses():
    message = MarkdownMessage(
        message_id="m_1",
        role=Role.user,
        text="hello",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert restored.text == "hello"


def test_deeplink_message_parses():
    message = DeeplinkCardMessage(
        message_id="m_2",
        role=Role.other,
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
        title="now",
        subtitle="the present",
        link="/chain/now",
        enabled=True,
    )
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert restored.link == "/chain/now"
    assert restored.enabled is True


def test_heartbeat_message_parses():
    message = HeartbeatMessage()
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert isinstance(restored, HeartbeatMessage)
    assert "message_id" not in message.model_dump()
    assert restored.role is Role.meta
    assert restored.type == "heartbeat"
