from dependency_injector import containers, providers

from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.clients.di.container import ClientsContainer
from take_home.causal_chains.agents.stores.causal_chain_store.graph_causal_chain_store import (
    GraphCausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.ddb_turn_store import DdbTurnStore
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    clients = providers.Container(ClientsContainer)
    stub_turn_runner = providers.Factory(StubTurnRunner)
    app_agent_runner = providers.Factory(
        AppAgentRunner,
        api_key=config.openai_api_key,
        memcache=clients.memcache,
    )
    agent_runner = providers.Selector(
        config.agent_runner,
        stub=stub_turn_runner,
        openai=app_agent_runner,
    )
    messaging_store = providers.Singleton(
        MessagingStoreImpl,
        dynamo_db=clients.dynamo_db,
    )
    turn_store = providers.Singleton(
        DdbTurnStore,
        dynamo_db=clients.dynamo_db,
    )
    causal_chain_store = providers.Singleton(
        GraphCausalChainStore,
        graph_db=clients.graph_db,
    )
    chat_service = providers.Singleton(
        ChatService,
        agent_runner=agent_runner,
        messaging_store=messaging_store,
        turn_store=turn_store,
    )
