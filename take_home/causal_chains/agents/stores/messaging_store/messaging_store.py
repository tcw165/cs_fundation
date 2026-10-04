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
from take_home.causal_chains.agents.models.messaging.protocol.message_base import (
    BaseMessage,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)


_SEARCH_PAGE_SIZE = 100


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
        limit: int,
        after_message: str | None = None,
        after_message_timestamp: datetime | None = None,
    ) -> MessagePage:
        """List one page of messages, oldest first.

        Args:
            conversation_id: Conversation to read.
            limit: Maximum number of messages in the page.
            after_message: Exclusive message id. The page starts after this
                message and does not include it. None starts at the oldest
                message.
            after_message_timestamp: created_timestamp of after_message. None
                when after_message is None. The page starts after
                MSG#{timestamp}#{message_id} and does not include that message.
        """
        exclusive_start_sk = None
        if after_message is not None:
            if after_message_timestamp is None:
                raise ValueError("after_message_timestamp is required")
            exclusive_start_sk = BaseMessage.message_sort_key(
                after_message_timestamp,
                after_message,
            )
            stored = self._dynamo_db.get_item(
                "conversation",
                {
                    "PK": f"CONV#{conversation_id}",
                    "SK": exclusive_start_sk,
                },
            )
            if stored is None:
                return MessagePage(messages=[])
        rows, next_sort_key = self._dynamo_db.query(
            "conversation",
            "PK",
            f"CONV#{conversation_id}",
            "SK",
            "MSG#",
            limit,
            exclusive_start_sk,
        )
        messages = [
            message_adapter.validate_python(row["message_json"])
            for row in rows
        ]
        if after_message is not None:
            messages = [
                message
                for message in messages
                if message.message_id != after_message
            ]
        next_cursor = None
        if next_sort_key is not None and messages:
            next_cursor = messages[-1].message_id
        return MessagePage(
            messages=messages,
            next_cursor=next_cursor,
        )

    @override
    async def search_messages(
        self,
        conversation_id: str,
        since: datetime,
        until: datetime,
    ) -> list[Message]:
        """Messages in the window, oldest first, inclusive of both ends."""
        exclusive_start_sk = f"MSG#{since.isoformat()}"
        found: list[Message] = []
        while True:
            rows, next_sort_key = self._dynamo_db.query(
                "conversation",
                "PK",
                f"CONV#{conversation_id}",
                "SK",
                "MSG#",
                _SEARCH_PAGE_SIZE,
                exclusive_start_sk,
            )
            for row in rows:
                message = message_adapter.validate_python(row["message_json"])
                if not isinstance(message, BaseMessage):
                    continue
                if message.created_timestamp < since:
                    continue
                if message.created_timestamp > until:
                    return found
                found.append(message)
            if next_sort_key is None:
                return found
            exclusive_start_sk = next_sort_key

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

    @override
    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        item = self._dynamo_db.get_item(
            "conversation",
            {"PK": f"CONV#{conversation_id}", "SK": "METADATA"},
        )
        if item is None:
            return None
        return Conversation.from_dynamodb(item)

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
