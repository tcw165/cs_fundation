from collections.abc import AsyncGenerator
from typing import override

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.crystal_ball.discover import (
    DiscoveryAction,
    advance,
    path_prompt,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.discovered_situations import (
    DiscoveredSituations,
)
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
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
            store = context.clients.causal_chain_store
            user_ask = "\n".join(inputs)
            root_result = Runner.run_streamed(
                now_scout,
                input=user_ask,
                context=context,
            )
            results.append(root_result)
            async for event in self._events(root_result):
                yield event
            root = root_result.final_output
            if not isinstance(root, Situation):
                yield SseError(message="now scout did not return a situation")
                return
            await store.add_situation(root)
            action = DiscoveryAction.discover
            for _attempt in range(context.run_config.attempt_quota):
                step = Runner.run_streamed(
                    path_builder,
                    input=path_prompt(
                        user_ask,
                        root.desc,
                        action,
                    ),
                    context=context,
                )
                results.append(step)
                async for event in self._events(step):
                    yield event
                found = step.final_output
                if not isinstance(found, DiscoveredSituations):
                    yield SseError(message="path builder did not return situations")
                    return
                action = advance(found, user_ask)
                if action is DiscoveryAction.stop:
                    break
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

    async def _events(
        self,
        result: object,
    ) -> AsyncGenerator[SseEvent]:
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
