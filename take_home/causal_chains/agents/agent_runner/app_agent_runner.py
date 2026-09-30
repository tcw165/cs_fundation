import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from functools import partial
from typing import override
import anyio
from agents import InputGuardrailTripwireTriggered, RunConfig, Runner, trace
from agents.run_config import CallModelData, ModelInputData
from anyio.streams.memory import MemoryObjectSendStream
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.agents.input_guardrail.input_guardrail_agent import (
    blocked_input_message,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    deeplink_message,
)
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.observability.logging import logger


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
    return HeartbeatMessage()


def _markdown(text: str) -> MarkdownMessage:
    return MarkdownMessage(
        message_id=str(uuid.uuid4()),
        role=Role.agent,
        text=text,
    )


def _tool_call_name(item: object) -> str:
    name = _raw_field(item, "name")
    if isinstance(name, str) and name:
        return name
    function = _raw_field(item, "function")
    if isinstance(function, dict):
        nested = function.get("name")
    else:
        nested = getattr(function, "name", None)
    return str(nested or "tool")


def _tool_call_id(item: object) -> str | None:
    for field_name in ("call_id", "id"):
        value = _raw_field(item, field_name)
        if isinstance(value, str) and value:
            return value
    return None


def _tool_call_arguments(item: object) -> object:
    raw = _raw_field(item, "arguments")
    if isinstance(raw, str) and raw.strip():
        return raw
    function = _raw_field(item, "function")
    if isinstance(function, dict):
        return function.get("arguments")
    return getattr(function, "arguments", None)


def _render_at_end(item: object) -> bool:
    raw = _tool_call_arguments(item)
    if not isinstance(raw, str) or not raw.strip():
        return True
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return True
    if not isinstance(payload, dict) or "render_at_end" not in payload:
        return True
    return bool(payload["render_at_end"])


def _card_from_output(output: object) -> DeeplinkCard:
    if isinstance(output, DeeplinkCard):
        return output
    if isinstance(output, str):
        return DeeplinkCard.model_validate_json(output)
    return DeeplinkCard.model_validate(output)


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
        logger().info(
            f"paragraph chars={len(paragraph)} prefix={paragraph[:80]}",
        )
        await send.send(_markdown(paragraph))
    if rest and buffer.strip():
        logger().info(
            f"paragraph chars={len(buffer.strip())} prefix={buffer.strip()[:80]}",
        )
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
                logger().info(
                    f"agent run start turn_id={context.turn_id} ask_len={len(user_ask)}",
                )
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
                # Call id to tool name for this turn. The output event only has the id.
                tool_names: dict[str, str] = {}
                render_later: dict[str, bool] = {}
                # Messages held until the story is finished, then sent in order.
                tail_messages: list[Message] = []
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
                        tool_name = _tool_call_name(item)
                        call_id = _tool_call_id(item)
                        logger().info(f"tool call {tool_name}")
                        if call_id is not None:
                            tool_names[call_id] = tool_name
                            if tool_names[call_id] == "show_deeplink_widget":
                                render_later[call_id] = _render_at_end(item)
                        continue
                    if (
                        event_type == "run_item_stream_event"
                        and getattr(item, "type", "") == "tool_call_output_item"
                    ):
                        call_id = _raw_field(item, "call_id")
                        if tool_names.get(str(call_id)) != "show_deeplink_widget":
                            continue
                        buffer = await _emit_paragraphs(send, buffer, rest=True)
                        message = deeplink_message(
                            _card_from_output(getattr(item, "output", None)),
                        )
                        if render_later.get(str(call_id), True):
                            logger().info("deeplink queued")
                            tail_messages.append(message)
                        else:
                            logger().info("deeplink sent")
                            await send.send(message)
                tail = buffer.strip()
                buffer = await _emit_paragraphs(send, buffer, rest=True)
                logger().info(
                    f"agent run end pending_deeplinks={len(tail_messages)} tail_flushed={bool(tail)}",
                )
                for message in tail_messages:
                    await send.send(message)
                self._memcache.flush()
        except InputGuardrailTripwireTriggered:
            logger().info("input guardrail triggered")
            self._memcache.flush()
            await send.send(_markdown(blocked_input_message))
        except Exception:
            logger().exception("agent run failed")
            raise
        finally:
            stop.set()
            await send.aclose()
