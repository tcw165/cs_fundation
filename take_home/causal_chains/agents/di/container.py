from dependency_injector import containers, providers

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.di.ping_postgres import ping_postgres
from take_home.causal_chains.agents.openai_runner.openai_turn_runner import OpenaiTurnRunner
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_ping = providers.Callable(
        ping_postgres,
        database_url=config.database_url,
    )
    stub_turn_runner = providers.Factory(StubTurnRunner)
    openai_turn_runner = providers.Factory(
        OpenaiTurnRunner,
        api_key=config.openai_api_key,
    )
    agent_runner = providers.Selector(
        config.agent_runner,
        stub=stub_turn_runner,
        openai=openai_turn_runner,
    )
    chat_service = providers.Singleton(
        ChatService,
        agent_runner=agent_runner,
    )
