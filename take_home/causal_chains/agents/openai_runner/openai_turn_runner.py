from collections.abc import AsyncIterator

from take_home.causal_chains.models.sse_event import SseDelta, SseDone, SseError, SseTool
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.protocol.turn_runner import SseEvent


class OpenaiTurnRunner:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        try:
            from agents import Agent, Runner
            from openai.types.responses import ResponseTextDeltaEvent
        except ImportError as error:
            yield SseError(message=str(error))
            return

        agent = Agent(
            name="causal_chains",
            instructions="You help explore financial causal chains. Be concise.",
        )
        result = Runner.run_streamed(agent, input=text)
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
            yield SseDone(message_id=f"m_{turn.turn_id}")
        except Exception as error:
            yield SseError(message=str(error))
        finally:
            cancel = getattr(result, "cancel", None)
            if cancel is not None:
                cancel()
