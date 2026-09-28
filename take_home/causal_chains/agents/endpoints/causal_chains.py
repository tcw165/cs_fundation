from fastapi import APIRouter

from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain

router = APIRouter()


@router.get("/causal_chains", response_model=list[CausalChain])
async def get_causal_chains(
    container: AppContainerDep,
) -> list[CausalChain]:
    return await container.causal_chain_store().get_chains()
