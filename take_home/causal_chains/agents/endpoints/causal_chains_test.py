import asyncio
from uuid import UUID

from dependency_injector import providers

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.endpoints.causal_chains import get_causal_chains
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import StartSituation


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


class _Chains:
    def __init__(
        self,
        chains: list[CausalChain],
    ) -> None:
        self._chains = chains

    async def get_chains(
        self,
    ) -> list[CausalChain]:
        return self._chains


def test_get_causal_chains_returns_every_root_chain():
    root = StartSituation(
        situation_id=NOW_ID,
        version=1,
        title="now",
        desc="now",
        potential_drivers=[],
        remained_drivers=[],
    )
    chain = CausalChain(situations=[root], links=[])
    container = AppContainer()
    container.causal_chain_store.override(providers.Object(_Chains([chain])))
    assert asyncio.run(get_causal_chains(container)) == [chain]
