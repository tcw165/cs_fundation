from collections.abc import AsyncGenerator
from typing import override

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.messaging.sse_event import (
    RunTraces,
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseTool,
)
from take_home.causal_chains.agents.models.run_context import RunContext


class AppAgentRunner(AgentRunner):
    def __init__(
        self,
        api_key: str,
        memcache: Memcache,
    ) -> None:
        self._api_key = api_key
        self._memcache = memcache

    @override
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AsyncGenerator[SseEvent]:
        results: list[object] = []
        try:
            user_ask = "\n".join(inputs)
            result = Runner.run_streamed(
                causal_chain,
                input=(
                    f"Future situation:\n{user_ask}\n"
                    f"Remaining attempts: {context.run_config.attempt_quota}"
                ),
                context=context,
            )
            results.append(result)
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
            if context.run_config.include_traces:
                yield RunTraces(text=self._memcache.flush())
            else:
                self._memcache.flush()
            yield SseDone(message_id=f"m_{context.turn_id}")
        except Exception as error:
            yield SseError(message=str(error))
        finally:
            for result in results:
                cancel = getattr(result, "cancel", None)
                if cancel is not None:
                    cancel()
