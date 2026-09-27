from collections.abc import AsyncGenerator, AsyncIterator

from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.models.messaging.sse_event import (
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseTool,
)
from take_home.causal_chains.agents.models.runner_context import RunnerContext
from take_home.causal_chains.models.turn import Turn


class OpenaiTurnRunner:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def stream(
        self,
        inputs: list[str],
        context: RunnerContext,
    ) -> AsyncGenerator[SseEvent]:
        agent = Agent(
            name="causal_chains",
            instructions="You help explore financial causal chains. Be concise.",
        )
        result = Runner.run_streamed(agent, input="\n".join(inputs))
        try:
            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    data = getattr(event, "data", None)
                    if isinstance(data, ResponseTextDeltaEvent):
                        yield SseDelta(text=data.delta)
                    continue
                if event.type == "run_item_stream_event":
                    item = getattr(event, "item", None)
                    item_type = getattr(item, "type", "")
                    if item_type == "tool_call_item":
                        name = getattr(getattr(item, "raw_item", None), "name", "tool")
                        yield SseTool(name=str(name), status="called")
            yield SseDone(message_id=f"m_{context.turn_id}")
        except Exception as error:
            yield SseError(message=str(error))
        finally:
            cancel = getattr(result, "cancel", None)
            if cancel is not None:
                cancel()

    async def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        context = RunnerContext(
            conversation_id=turn.conversation_id,
            turn_id=turn.turn_id,
        )
        async for event in self.stream([text], context):
            yield event
