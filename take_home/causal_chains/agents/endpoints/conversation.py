from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from take_home.causal_chains.agents.chat_service.chat_service import format_sse
from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.models.turn import Turn

router = APIRouter()


@router.post("/conversation/{conversation_id}/messages", response_model=Turn)
async def post_message(
    conversation_id: str,
    body: PostMessageBody,
    container: AppContainerDep,
) -> Turn:
    return container.chat_service().post_message(conversation_id, body.text)


@router.get("/conversation/{conversation_id}/turn/{turn_id}/sse")
async def turn_sse(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
) -> StreamingResponse:
    async def event_stream():
        async for event in container.chat_service().subscribe(conversation_id, turn_id):
            yield format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
