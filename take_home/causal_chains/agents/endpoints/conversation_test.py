import asyncio

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.endpoints.conversation import turn_sse
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus


class _ChainStore:
    pass


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}
        self.put_item("conversation", {"conversation_id": "1", "messages": []})

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        key = (("conversation_id", item["conversation_id"]),)
        self._items[(table_name, key)] = item

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        stored_key = tuple(sorted(key.items()))
        return self._items.get((table_name, stored_key))


def test_chat_service_post_returns_queued_turn():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb())
        turn_store = InMemoryTurnStore()
        service = ChatService(StubTurnRunner(), store, turn_store, _ChainStore())
        turn = await service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        await service.run_turn(turn, "hello")
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        stored = await store.list_messages("1")
        saved = await turn_store.get_turn(turn.turn_id)
        return turn, events, stored, saved

    turn, events, stored, saved = asyncio.run(exercise())
    assert any(event.type == "markdown" for event in events)
    assert events[-1].type == "done"
    assert len(stored) == 1
    assert stored[0].text == "hello"
    assert saved is not None
    assert saved.status is TurnStatus.completed


def test_turn_sse_passes_include_traces_to_subscribe():
    class _Container:
        def __init__(self, service: ChatService) -> None:
            self._service = service

        def chat_service(self) -> ChatService:
            return self._service

    async def exercise():
        service = ChatService(
            StubTurnRunner(),
            MessagingStoreImpl(_FakeDynamoDb()),
            InMemoryTurnStore(),
            _ChainStore(),
        )
        turn = await service.post_message("1", "hello")
        await service.run_turn(turn, "hello")
        response = await turn_sse(
            "1",
            turn.turn_id,
            _Container(service),
            include_traces=True,
        )
        async for _chunk in response.body_iterator:
            pass
        return service._contexts[turn.turn_id]

    context = asyncio.run(exercise())
    assert context.run_config.include_traces is True
