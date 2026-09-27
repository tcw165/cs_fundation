from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import StreamingResponse

from take_home.causal_chains.agents.chat_service.chat_service import format_sse
from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.models.turn import Turn

router = APIRouter()


@router.post("/conversation/{conversation_id}/messages", response_model=Turn)
async def post_message(
    conversation_id: str,
    body: PostMessageBody,
    container: AppContainerDep,
    background_tasks: BackgroundTasks,
) -> Turn:
    service = container.chat_service()
    turn = service.post_message(conversation_id, body.text)
    background_tasks.add_task(service.run_turn, turn, body.text)
    return turn


@router.get("/conversation/{conversation_id}/turn/{turn_id}/sse")
async def turn_sse(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
    include_traces: Annotated[bool, Query()] = False,
) -> StreamingResponse:
    chat_service = container.chat_service()

    async def event_stream():
        async for event in chat_service.subscribe(
            conversation_id=conversation_id,
            turn_id=turn_id,
            run_config=RunConfig(
                include_traces=include_traces,
            ),
        ):
            yield format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
