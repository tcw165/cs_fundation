from fastapi import FastAPI

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.di.deps import get_app_container
from take_home.causal_chains.agents.endpoints import health


def create_app(container: AppContainer) -> FastAPI:
    """Build the FastAPI app around one injected AppContainer.

    The container is the process composition root (one graph, one lifetime).
    Endpoints never construct AppContainer; they take AppContainerDep.
    """
    app = FastAPI()
    # App singleton: anything that has the Request (middleware, lifespan,
    # background tasks) can read the same graph via app.state. Not used by
    # Depends() itself — that is the override below.
    app.state.app_container = container
    # FastAPI Depends lookup: AppContainerDep -> get_app_container. Without
    # this override, get_app_container raises. Tests pass a different
    # container into create_app and get the same binding automatically.
    app.dependency_overrides[get_app_container] = lambda: container
    app.include_router(health.router)
    return app
