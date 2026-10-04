from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.messaging.protocol.message_base import (
    BaseMessage,
)
from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Role,
    SystemMessage,
    message_adapter,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)


def test_markdown_message_parses():
    message = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
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
        conversation_id="1",
        user_uuid="user-1",
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


def test_system_message_parses():
    message = SystemMessage(
        message_id="m_timeout",
        conversation_id="1",
        user_uuid="user-1",
        text="This turn timed out. Send your message again.",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    restored = message_adapter.validate_python(message.model_dump())
    assert isinstance(restored, SystemMessage)
    assert restored.role is Role.system
    assert restored.kind == "system"
    assert restored.to_openai_message()["role"] == "system"
    assert restored.to_openai_message()["content"] == message.text


def test_heartbeat_message_parses():
    message = HeartbeatMessage()
    restored = message_adapter.validate_python(message.model_dump())
    assert restored == message
    assert isinstance(restored, HeartbeatMessage)
    assert "message_id" not in message.model_dump()
    assert restored.role is Role.meta
    assert restored.kind == "heartbeat"


def test_message_item_uses_one_key_for_the_same_id_and_timestamp():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    message = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="hello",
        created_timestamp=created,
    )
    first = message.to_dynamodb()
    second = message.to_dynamodb()
    assert first["SK"] == second["SK"]
    assert first["SK"] == BaseMessage.message_sort_key(created, "m_1")
    assert first["created_at"] == created.isoformat()
    assert first["schema_version"] == 1
    assert "input_guardrail_flagged" not in first["message_json"]


def test_same_message_id_compares_and_hashes_equal():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    first = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="one",
        created_timestamp=created,
    )
    second = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.agent,
        text="two",
        created_timestamp=created,
    )
    assert first == second
    assert hash(first) == hash(second)


def test_openai_message_uses_user_or_assistant():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    user = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="hello",
        created_timestamp=created,
    )
    agent = DeeplinkCardMessage(
        message_id="m_2",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.other,
        title="now",
        subtitle="the present",
        link="/chain/now",
        enabled=True,
        created_timestamp=created,
    )
    assert user.to_openai_message()["role"] == "user"
    assert user.to_openai_message()["content"] == "hello"
    assert agent.to_openai_message()["role"] == "assistant"
    assert agent.to_openai_message()["content"] == "now"


def test_payload_that_says_type_does_not_parse():
    with pytest.raises(ValidationError):
        message_adapter.validate_python(
            {
                "type": "markdown",
                "message_id": "m_1",
                "role": "user",
                "text": "hello",
                "created_timestamp": "2026-09-30T00:00:00Z",
            }
        )
