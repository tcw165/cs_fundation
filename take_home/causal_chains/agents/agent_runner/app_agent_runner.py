import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from functools import partial
from typing import override
from urllib.parse import quote

import anyio
from agents import RunConfig, Runner, trace
from agents.run_config import CallModelData, ModelInputData
from anyio.streams.memory import MemoryObjectSendStream
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.message import (
    DeeplinkCardMessage,
    HeartbeatMessage,
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.run_context import RunContext


def _make_current_time_reminder_message(moment: datetime) -> dict[str, str]:
    return {
        "role": "assistant",
        "content": f"Current time: {moment.isoformat()} {moment.tzname()}",
    }


def _decorate_tail_messages(data: CallModelData[RunContext]) -> ModelInputData:
    note = _make_current_time_reminder_message(data.context.clock.now())
    items = list(data.model_data.input)
    user_at = next(
        index
        for index in range(len(items) - 1, -1, -1)
        if items[index].get("role") == "user"
    )
    previous = user_at - 1
    if (
        previous >= 0
        and items[previous].get("role") == "assistant"
        and str(items[previous].get("content", "")).startswith("Current time:")
    ):
        items[previous] = note
    else:
        items.insert(user_at, note)
    return ModelInputData(input=items, instructions=data.model_data.instructions)


def _raw_field(
    item: object,
    field_name: str,
) -> object:
    raw_item = getattr(item, "raw_item", None)
    if isinstance(raw_item, dict):
        return raw_item.get(field_name)
    return getattr(raw_item, field_name, None)


_HEARTBEAT_INTERVAL_S = 3.0


def _heartbeat() -> HeartbeatMessage:
    return HeartbeatMessage(message_id=str(uuid.uuid4()))


def _markdown(text: str) -> MarkdownMessage:
    return MarkdownMessage(
        message_id=str(uuid.uuid4()),
        role=Role.agent,
        text=text,
    )


def _deeplink_link(card: DeeplinkCard) -> str:
    title = quote(card.title, safe="")
    return f"/chain/{card.root_situation_id}/{card.root_version}?title={title}"


def _deeplink_message(output: object) -> DeeplinkCardMessage:
    if isinstance(output, DeeplinkCard):
        card = output
    elif isinstance(output, str):
        card = DeeplinkCard.model_validate_json(output)
    else:
        card = DeeplinkCard.model_validate(output)
    return DeeplinkCardMessage(
        message_id=str(uuid.uuid4()),
        role=Role.other,
        link=_deeplink_link(card),
    )


def _ready_paragraphs(buffer: str) -> tuple[list[str], str]:
    if "\n\n" not in buffer:
        return [], buffer
    parts = buffer.split("\n\n")
    ready = [part for part in parts[:-1] if part.strip()]
    return ready, parts[-1]


async def _emit_paragraphs(
    send: MemoryObjectSendStream[Message],
    buffer: str,
    *,
    rest: bool,
) -> str:
    ready, buffer = _ready_paragraphs(buffer)
    for paragraph in ready:
        await send.send(_markdown(paragraph))
    if rest and buffer.strip():
        await send.send(_markdown(buffer))
        return ""
    return buffer


async def stream_heartbeat(
    send: MemoryObjectSendStream[Message],
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
                await send.send(_heartbeat())
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
        interval_s: float = _HEARTBEAT_INTERVAL_S,
    ) -> AsyncGenerator[Message]:
        results: list[object] = []
        send, receive = anyio.create_memory_object_stream[Message]()
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
                    async for message in receive:
                        yield message
        finally:
            for result in results:
                cancel = getattr(result, "cancel", None)
                if cancel is not None:
                    cancel()

    async def _stream_agent_run(
        self,
        inputs: list[str],
        context: RunContext,
        send: MemoryObjectSendStream[Message],
        stop: anyio.Event,
        results: list[object],
    ) -> None:
        try:
            with trace(
                "app_agent_runner",
                group_id=context.conversation_id,
                metadata={"turn_id": context.turn_id},
            ):
                user_ask = "\n".join(inputs)
                result = Runner.run_streamed(
                    causal_chain,
                    input=user_ask,
                    context=context,
                    max_turns=context.run_config.causal_chain_max_steps,
                    run_config=RunConfig(
                        call_model_input_filter=_decorate_tail_messages,
                    ),
                )
                results.append(result)
                tool_names: dict[str, str] = {}
                buffer = ""
                async for event in result.stream_events():
                    event_type = getattr(event, "type", "")
                    if event_type == "raw_response_event":
                        data = getattr(event, "data", None)
                        if isinstance(data, ResponseTextDeltaEvent):
                            buffer += data.delta
                            buffer = await _emit_paragraphs(send, buffer, rest=False)
                        continue
                    item = getattr(event, "item", None)
                    if (
                        event_type == "run_item_stream_event"
                        and getattr(item, "type", "") == "tool_call_item"
                    ):
                        buffer = await _emit_paragraphs(send, buffer, rest=True)
                        name = _raw_field(item, "name")
                        call_id = _raw_field(item, "call_id")
                        if isinstance(call_id, str):
                            tool_names[call_id] = str(name or "tool")
                        continue
                    if (
                        event_type == "run_item_stream_event"
                        and getattr(item, "type", "") == "tool_call_output_item"
                    ):
                        call_id = _raw_field(item, "call_id")
                        if tool_names.get(str(call_id)) != "make_deeplink_widget":
                            continue
                        buffer = await _emit_paragraphs(send, buffer, rest=True)
                        await send.send(
                            _deeplink_message(getattr(item, "output", None)),
                        )
                buffer = await _emit_paragraphs(send, buffer, rest=True)
                self._memcache.flush()
        finally:
            stop.set()
            await send.aclose()
