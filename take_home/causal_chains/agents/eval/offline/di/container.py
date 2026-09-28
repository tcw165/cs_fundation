from decoy import Decoy
from dependency_injector import containers, providers

from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.eval.offline.di.rehearsal import rehearse_persistence
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore


class EvalContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    decoy = providers.Singleton(Decoy)
    memcache = providers.Singleton(InMemoryMemcache)
    messaging_store = providers.Singleton(
        lambda decoy: decoy.mock(cls=MessagingStore),
        decoy,
    )
    turn_store = providers.Singleton(
        lambda decoy: decoy.mock(cls=TurnStore),
        decoy,
    )
    causal_chain_store = providers.Singleton(
        lambda decoy: decoy.mock(cls=CausalChainStore),
        decoy,
    )
    app_agent_runner = providers.Singleton(
        AppAgentRunner,
        api_key=config.openai_api_key,
        memcache=memcache,
    )
    chat_service = providers.Singleton(
        ChatService,
        agent_runner=app_agent_runner,
        messaging_store=messaging_store,
        turn_store=turn_store,
        causal_chain_store=causal_chain_store,
    )

    def __new__(cls, **overriding_providers: object) -> containers.DynamicContainer:
        container = super().__new__(cls, **overriding_providers)
        rehearse_persistence(
            container.decoy(),
            container.messaging_store(),
            container.turn_store(),
            container.causal_chain_store(),
        )
        return container
