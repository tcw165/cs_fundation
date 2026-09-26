from dependency_injector import containers, providers

from take_home.causal_chains.agents.di.ping_postgres import ping_postgres


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_ping = providers.Callable(
        ping_postgres,
        database_url=config.database_url,
    )
