import json
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime, timezone
from functools import partial
from typing import override

import anyio
from anyio.streams.memory import MemoryObjectSendStream

from agents import (
    InputGuardrailTripwireTriggered,
    RunConfig,
    RunResultStreaming,
    Runner,
    trace,
)
from agents.run_config import CallModelData, ModelInputData
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agent_runner.protocol.agent_stream import AgentStream
from take_home.causal_chains.agents.agents.chief_of_staff.chief_of_staff import (  # pragma: allowlist secret
    build_chief_of_staff,
)
from take_home.causal_chains.agents.agents.input_guardrail.input_guardrail_agent import (
    blocked_input_message,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import (
    DeeplinkCard,
    DeeplinkResult,
)
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    deeplink_message,
)
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.observability.logging import logger

_WIDGET_TOOLS = (
    "show_deeplink_widget",
    "deeplinks_finder",
)


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


def _markdown(text: str, conversation_id: str) -> MarkdownMessage:
    return MarkdownMessage(
        message_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_uuid="user-1",
        role=Role.agent,
        text=text,
        created_timestamp=datetime.now(timezone.utc),
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


def _cards_from_finder_output(output: object) -> list[DeeplinkCard]:
    if isinstance(output, DeeplinkResult):
        return list(output.deeplinks)
    if isinstance(output, str):
        return list(DeeplinkResult.model_validate_json(output).deeplinks)
    return list(DeeplinkResult.model_validate(output).deeplinks)


def _queue_deeplink(
    tail_messages: list[Message],
    seen_links: set[str],
    card: DeeplinkCard,
    conversation_id: str,
) -> None:
    message = deeplink_message(card, conversation_id)
    if message.link in seen_links:
        return
    seen_links.add(message.link)
    logger().info("deeplink queued")
    tail_messages.append(message)


def _ready_paragraphs(buffer: str) -> tuple[list[str], str]:
    if "\n\n" not in buffer:
        return [], buffer
    parts = buffer.split("\n\n")
    ready = [part for part in parts[:-1] if part.strip()]
    return ready, parts[-1]


async def _emit_paragraphs(
    send: MemoryObjectSendStream[Message],
    buffer: str,
    conversation_id: str,
    *,
    rest: bool,
) -> str:
    ready, buffer = _ready_paragraphs(buffer)
    for paragraph in ready:
        logger().info(
            f"paragraph chars={len(paragraph)} prefix={paragraph[:80]}",
        )
        await send.send(_markdown(paragraph, conversation_id))
    if rest and buffer.strip():
        logger().info(
            f"paragraph chars={len(buffer.strip())} prefix={buffer.strip()[:80]}",
        )
        await send.send(_markdown(buffer, conversation_id))
        return ""
    return buffer


class AppAgentRunner(AgentRunner):
    def __init__(
        self,
        api_key: str,
        memcache: Memcache,
    ) -> None:
        self._api_key = api_key
        self._memcache = memcache

    def _stream_agent_run(
        self,
        inputs: list[Message],
        context: RunContext,
    ) -> RunResultStreaming:
        model_input = [message.to_openai_message() for message in inputs]
        logger().info(
            "agent run start "
            f"conversation_id={context.conversation_id} "
            f"turn_id={context.turn_id} "
            f"ask_len={sum(len(message.openai_text()) for message in inputs)}",
        )
        agent = build_chief_of_staff(
            conversation_id=context.conversation_id,
            messaging_store=context.clients.messaging_store,
            clock=context.clock,
        )
        return Runner.run_streamed(
            agent,
            input=model_input,
            context=context,
            max_turns=context.run_config.causal_chain_max_steps,
            run_config=RunConfig(
                call_model_input_filter=_decorate_tail_messages,
            ),
        )

    @override
    async def stream(
        self,
        inputs: list[Message],
        context: RunContext,
    ) -> AgentStream:
        runner = self

        class AppAgentStream(AgentStream):
            def __init__(self) -> None:
                self._run_result: RunResultStreaming | None = None
                self._generator: AsyncGenerator[Message, None] | None = None

            def cancel(self) -> None:
                logger().info(f"agent run cancel turn_id={context.turn_id}")
                if self._run_result is not None:
                    self._run_result.cancel()

            def __aiter__(self) -> AsyncIterator[Message]:
                self._generator = self._read()
                return self._generator

            async def aclose(self) -> None:
                self.cancel()
                if self._generator is not None:
                    await self._generator.aclose()

            async def _read(self) -> AsyncGenerator[Message, None]:
                # Keep this trace open until the model stream is consumed. Closing it
                # after run_streamed returns drops the parent of every later span.
                with trace(
                    "app_agent_runner",
                    group_id=context.conversation_id,
                    metadata={"turn_id": context.turn_id},
                ):
                    self._run_result = runner._stream_agent_run(inputs, context)
                    send, receive = anyio.create_memory_object_stream[Message]()
                    async with anyio.create_task_group() as group:
                        group.start_soon(
                            partial(
                                runner._stream_messages,
                                self._run_result,
                                context,
                                send.clone(),
                            ),
                        )
                        await send.aclose()
                        async with receive:
                            async for message in receive:
                                yield message

        return AppAgentStream()

    async def _stream_messages(
        self,
        run_result: RunResultStreaming,
        context: RunContext,
        send: MemoryObjectSendStream[Message],
    ) -> None:
        try:
            # Call id to tool name for this turn. The output event only has the id.
            tool_names: dict[str, str] = {}
            render_later: dict[str, bool] = {}
            # Messages held until the story is finished, then sent in order.
            tail_messages: list[Message] = []
            seen_links: set[str] = set()
            buffer = ""
            async for event in run_result.stream_events():
                event_type = getattr(event, "type", "")
                if event_type == "raw_response_event":
                    data = getattr(event, "data", None)
                    if isinstance(data, ResponseTextDeltaEvent):
                        buffer += data.delta
                        buffer = await _emit_paragraphs(
                            send,
                            buffer,
                            context.conversation_id,
                            rest=False,
                        )
                    continue
                item = getattr(event, "item", None)
                if (
                    event_type == "run_item_stream_event"
                    and getattr(item, "type", "") == "tool_call_item"
                ):
                    buffer = await _emit_paragraphs(
                        send,
                        buffer,
                        context.conversation_id,
                        rest=True,
                    )
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
                    call_id = _tool_call_id(item) or ""
                    tool_name = tool_names.get(call_id)
                    if tool_name not in _WIDGET_TOOLS:
                        continue
                    buffer = await _emit_paragraphs(
                        send,
                        buffer,
                        context.conversation_id,
                        rest=True,
                    )
                    output = getattr(item, "output", None)
                    cards = (
                        _cards_from_finder_output(output)
                        if tool_name == "deeplinks_finder"
                        else [_card_from_output(output)]
                    )
                    hold = (
                        tool_name == "deeplinks_finder"
                        or render_later.get(call_id, True)
                    )
                    for card in cards:
                        if hold:
                            _queue_deeplink(
                                tail_messages,
                                seen_links,
                                card,
                                context.conversation_id,
                            )
                            continue
                        message = deeplink_message(card, context.conversation_id)
                        if message.link in seen_links:
                            continue
                        seen_links.add(message.link)
                        logger().info("deeplink sent")
                        await send.send(message)
            tail = buffer.strip()
            buffer = await _emit_paragraphs(
                send,
                buffer,
                context.conversation_id,
                rest=True,
            )
            logger().info(
                f"agent run end pending_deeplinks={len(tail_messages)} tail_flushed={bool(tail)}",
            )
            for message in tail_messages:
                await send.send(message)
            self._memcache.flush()
        except InputGuardrailTripwireTriggered:
            logger().info("input guardrail triggered")
            self._memcache.flush()
            await send.send(_markdown(blocked_input_message, context.conversation_id))
        except Exception:
            logger().exception("agent run failed")
            raise
        finally:
            await send.aclose()
