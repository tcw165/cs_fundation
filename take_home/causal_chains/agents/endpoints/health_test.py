from dependency_injector import providers

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.endpoints.health import health


def test_health_reports_up_when_db_ping_succeeds():
    container = AppContainer()
    with container.db_ping.override(providers.Object(True)):
        report = health(container)
    assert report.status == "ok"
    assert report.db == "up"


def test_health_reports_down_when_db_ping_fails():
    container = AppContainer()
    with container.db_ping.override(providers.Object(False)):
        report = health(container)
    assert report.status == "ok"
    assert report.db == "down"
