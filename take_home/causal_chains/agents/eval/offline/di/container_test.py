import asyncio
import inspect
from decimal import Decimal
from uuid import uuid4

from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.eval.offline.di import container as container_module
from take_home.causal_chains.agents.eval.offline.di.container import EvalContainer
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


def test_eval_container_wires_the_real_runner_to_store_mocks() -> None:
    container = EvalContainer()
    container.config.openai_api_key.from_value("test-key")
    runner = container.app_agent_runner()
    store = container.causal_chain_store()
    service = container.chat_service()
    source = inspect.getsource(container_module)

    assert isinstance(runner, AppAgentRunner)
    assert container.app_agent_runner() is runner
    assert isinstance(store, CausalChainStore)
    assert isinstance(service, ChatService)
    assert service._agent_runner is runner
    assert "boto3" not in source
    assert "neo4j" not in source


def test_rehearsed_stores_return_what_they_saved() -> None:
    container = EvalContainer()
    root = Situation(
        situation_id=uuid4(),
        version=1,
        desc="now",
        is_root=True,
    )
    later = Situation(
        situation_id=uuid4(),
        version=1,
        desc="later",
        is_root=False,
    )
    link = LeadsTo(
        from_situation_id=root.situation_id,
        from_version=root.version,
        to_situation_id=later.situation_id,
        to_version=later.version,
        p=Decimal("1"),
    )
    message = MarkdownMessage(
        message_id="m_1",
        role=Role.user,
        text="hormuz",
    )
    other = message.model_copy(update={"message_id": "m_2"})
    turn = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message="m_1",
    )

    async def round_trip() -> None:
        messaging_store = container.messaging_store()
        turn_store = container.turn_store()
        causal_chain_store = container.causal_chain_store()
        await messaging_store.append("1", message)
        await messaging_store.append("2", other)
        await turn_store.put_turn(turn)
        await causal_chain_store.add_situation(root)
        await causal_chain_store.link_situations(root, later, link)
        listed = await messaging_store.list_messages("1")
        missing = await turn_store.get_turn("missing")
        stored_turn = await turn_store.get_turn("t_1")
        chains = await causal_chain_store.get_chains()
        assert [item.text for item in listed] == ["hormuz"]
        assert missing is None
        assert stored_turn == turn
        assert len(chains) == 1
        assert chains[0].situations == [root, later]
        assert chains[0].links == [link]

    asyncio.run(round_trip())
