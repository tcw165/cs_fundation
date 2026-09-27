from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.endpoints.health import health


def test_health_reports_ready_when_container_is_bound():
    report = health(AppContainer())
    assert report.model_dump() == {"status": "ok"}
