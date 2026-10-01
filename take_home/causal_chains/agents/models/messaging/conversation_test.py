from datetime import datetime, timezone

from take_home.causal_chains.agents.models.messaging.conversation import Conversation
from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)
from take_home.causal_chains.agents.models.messaging.entry_context import MyBlog
from take_home.causal_chains.agents.models.messaging.followup_question import (
    TextFollowupQuestion,
    UriFollowupQuestion,
)
from take_home.causal_chains.agents.models.messaging.plan import Plan, PlanStatus, PlanStep


def _conversation(**overrides: object) -> Conversation:
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    values: dict[str, object] = {
        "id": "1",
        "user_uuid": "user-1",
        "title": "Strait of Hormuz",
        "status": ConversationStatus.OPEN,
        "entry_context": MyBlog(
            source_url="https://example.com/post",
            source_ip="203.0.113.4",
        ),
        "created_at": created,
    }
    values.update(overrides)
    return Conversation.model_validate(values)


def test_metadata_item_round_trips_plan_and_followups():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    conversation = _conversation(
        followup_questions=[
            TextFollowupQuestion(content="What happens next?"),
            UriFollowupQuestion(preview="Open", source_uri="https://example.com/more"),
        ],
        active_plan=Plan(
            id="p1",
            status=PlanStatus.PENDING,
            steps=[PlanStep(id="s1", goal="Open the strait")],
            created_at=created,
            updated_at=created,
        ),
        memory="Keep the opening in view.",
    )
    restored = Conversation.from_dynamodb(conversation.to_dynamodb())
    assert restored.model_dump() == conversation.model_dump()
    item = conversation.to_dynamodb()
    assert item["PK"] == "CONV#1"
    assert item["SK"] == "METADATA"
    assert item["schema_version"] == 1


def test_same_id_compares_and_hashes_equal():
    first = _conversation(title="One")
    second = _conversation(title="Two")
    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_openai_message_is_system_and_starts_with_title():
    message = _conversation(memory="A note.").to_openai_message()
    assert message["role"] == "system"
    assert message["type"] == "message"
    assert str(message["content"]).startswith("Strait of Hormuz")
