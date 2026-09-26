from fastapi import APIRouter

from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.http_models.health_response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(container: AppContainerDep) -> HealthResponse:
    return HealthResponse(status="ok", db="up" if container.db_ping() else "down")
