from take_home.causal_chains.agents.di.ping_postgres import ping_postgres


def test_ping_postgres_returns_false_for_invalid_url():
    assert ping_postgres("postgresql://nobody@127.0.0.1:1/missing") is False
