from datetime import datetime
from typing import override

from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
from take_home.causal_chains.agents.models.messaging.conversation import Conversation
from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)
from take_home.causal_chains.agents.models.messaging.entry_context import MyBlog
from take_home.causal_chains.agents.models.messaging.message import (
    Message,
    message_adapter,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)


class MessagingStoreImpl(MessagingStore):
    def __init__(
        self,
        dynamo_db: DynamoDb,
        user_uuid: str,
    ) -> None:
        self._dynamo_db = dynamo_db
        self._user_uuid = user_uuid

    @override
    async def append(
        self,
        conversation_id: str,
        message: Message,
    ) -> None:
        self._put_metadata_if_absent(conversation_id, message.created_timestamp)
        self._dynamo_db.put_item("conversation", message.to_dynamodb())

    @override
    async def list_messages(
        self,
        conversation_id: str,
    ) -> list[Message]:
        rows = self._dynamo_db.query(
            "conversation",
            "PK",
            f"CONV#{conversation_id}",
            "SK",
            "MSG#",
        )
        return [
            message_adapter.validate_python(row["message_json"])
            for row in rows
        ]

    @override
    async def save_message_with_ttl(
        self,
        conversation_id: str,
        message: Message,
        time_to_live: int,
    ) -> None:
        self._put_metadata_if_absent(conversation_id, message.created_timestamp)
        item = message.to_dynamodb()
        item["time_to_live"] = time_to_live
        self._dynamo_db.put_item("conversation", item)

    @override
    async def list_conversations(
        self,
        user_uuid: str,
    ) -> list[Conversation]:
        rows = self._dynamo_db.query_index(
            "conversation",
            "conversation_user_uuid",
            "conversation_user_uuid",
            user_uuid,
        )
        return [Conversation.from_dynamodb(row) for row in rows]

    def _put_metadata_if_absent(
        self,
        conversation_id: str,
        created_at: datetime,
    ) -> None:
        key = {"PK": f"CONV#{conversation_id}", "SK": "METADATA"}
        if self._dynamo_db.get_item("conversation", key) is not None:
            return
        conversation = Conversation(
            id=conversation_id,
            user_uuid=self._user_uuid,
            title="",
            status=ConversationStatus.OPEN,
            entry_context=MyBlog(source_url="", source_ip=""),
            created_at=created_at,
        )
        self._dynamo_db.put_item("conversation", conversation.to_dynamodb())
