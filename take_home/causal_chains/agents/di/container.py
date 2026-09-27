from dependency_injector import containers, providers

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.di.ping_postgres import ping_postgres
from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_ping = providers.Callable(
        ping_postgres,
        database_url=config.database_url,
    )
    stub_turn_runner = providers.Factory(StubTurnRunner)
    app_agent_runner = providers.Factory(
        AppAgentRunner,
        api_key=config.openai_api_key,
    )
    agent_runner = providers.Selector(
        config.agent_runner,
        stub=stub_turn_runner,
        openai=app_agent_runner,
    )
    chat_service = providers.Singleton(
        ChatService,
        agent_runner=agent_runner,
    )
