import pytest

from take_home.causal_chains.agents.di.deps import get_app_container


def test_get_app_container_raises_when_unbound():
    with pytest.raises(RuntimeError, match="AppContainer not bound"):
        get_app_container()
