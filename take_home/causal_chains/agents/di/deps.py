from typing import Annotated

from fastapi import Depends

from take_home.causal_chains.agents.di.container import AppContainer


def get_app_container() -> AppContainer:
    """Default provider. Must not resolve a real container.

    FastAPI calls this unless create_app binds dependency_overrides.
    Raising here makes a missing override fail at request time instead of
    silently constructing a second AppContainer.
    """
    raise RuntimeError("AppContainer not bound; create_app must set dependency_overrides")


AppContainerDep = Annotated[AppContainer, Depends(get_app_container)]
