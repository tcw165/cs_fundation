from collections.abc import AsyncGenerator
from functools import partial
from typing import override

import anyio
from agents import Runner, trace
from anyio.streams.memory import MemoryObjectSendStream
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.sse_event import (
    DeeplinkWidget,
    RunTraces,
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseHeartbeat,
    SseTool,
)
from take_home.causal_chains.agents.models.run_context import RunContext


def _raw_field(
    item: object,
    field_name: str,
) -> object:
    raw_item = getattr(item, "raw_item", None)
    if isinstance(raw_item, dict):
        return raw_item.get(field_name)
    return getattr(raw_item, field_name, None)


def _map_model_event(
    event: object,
) -> SseEvent | None:
    event_type = getattr(event, "type", "")
    if event_type == "raw_response_event":
        data = getattr(event, "data", None)
        if isinstance(data, ResponseTextDeltaEvent):
            return SseDelta(text=data.delta)
        return None
    if event_type == "run_item_stream_event":
        item = getattr(event, "item", None)
        if getattr(item, "type", "") == "tool_call_item":
            name = _raw_field(item, "name")
            return SseTool(name=str(name or "tool"), status="called")
    return None


def _deeplink_widget(
    output: object,
) -> DeeplinkWidget:
    if isinstance(output, DeeplinkCard):
        return DeeplinkWidget(card=output)
    if isinstance(output, str):
        return DeeplinkWidget(card=DeeplinkCard.model_validate_json(output))
    return DeeplinkWidget(card=DeeplinkCard.model_validate(output))


async def stream_heartbeat(
    send: MemoryObjectSendStream[SseEvent],
    stop: anyio.Event,
    interval_s: float,
) -> None:
    try:
        while not stop.is_set():
            with anyio.move_on_after(interval_s):
                await stop.wait()
            if stop.is_set():
                return
            try:
                await send.send(SseHeartbeat())
            except (anyio.BrokenResourceError, anyio.ClosedResourceError):
                return
    finally:
        await send.aclose()


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
        interval_s: float = 5.0,
    ) -> AsyncGenerator[SseEvent]:
        results: list[object] = []
        send, receive = anyio.create_memory_object_stream[SseEvent]()
        stop = anyio.Event()
        try:
            async with anyio.create_task_group() as group:
                group.start_soon(
                    partial(
                        self._stream_agent_run,
                        inputs=inputs,
                        context=context,
                        send=send.clone(),
                        stop=stop,
                        results=results,
                    ),
                )
                group.start_soon(
                    partial(
                        stream_heartbeat,
                        send=send.clone(),
                        stop=stop,
                        interval_s=interval_s,
                    ),
                )
                await send.aclose()
                async with receive:
                    async for event in receive:
                        yield event
                        if event.type in {"done", "error"}:
                            break
        finally:
            for result in results:
                cancel = getattr(result, "cancel", None)
                if cancel is not None:
                    cancel()

    async def _stream_agent_run(
        self,
        inputs: list[str],
        context: RunContext,
        send: MemoryObjectSendStream[SseEvent],
        stop: anyio.Event,
        results: list[object],
    ) -> None:
        try:
            try:
                with trace(
                    "app_agent_runner",
                    group_id=context.conversation_id,
                    metadata={"turn_id": context.turn_id},
                ):
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
                    tool_names: dict[str, str] = {}
                    async for event in result.stream_events():
                        mapped = _map_model_event(event)
                        if mapped is not None:
                            if mapped.type == "tool":
                                item = getattr(event, "item", None)
                                call_id = _raw_field(item, "call_id")
                                if isinstance(call_id, str):
                                    tool_names[call_id] = mapped.name
                            await send.send(mapped)
                            continue
                        item = getattr(event, "item", None)
                        if (
                            getattr(event, "type", "") == "run_item_stream_event"
                            and getattr(item, "type", "") == "tool_call_output_item"
                        ):
                            call_id = _raw_field(item, "call_id")
                            if tool_names.get(str(call_id)) == "make_deeplink_widget":
                                await send.send(
                                    _deeplink_widget(getattr(item, "output", None)),
                                )
                    if context.run_config.include_traces:
                        await send.send(RunTraces(text=self._memcache.flush()))
                    else:
                        self._memcache.flush()
                    stop.set()
                    await send.send(SseDone(message_id=f"m_{context.turn_id}"))
            except Exception as error:
                stop.set()
                await send.send(SseError(message=str(error)))
        finally:
            stop.set()
            await send.aclose()
