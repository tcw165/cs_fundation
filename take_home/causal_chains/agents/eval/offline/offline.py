import asyncio
import os
import uuid

import click
from agents import set_default_openai_client, set_trace_processors
from agents.tracing import TracingProcessor
from braintrust import init_logger
from braintrust.integrations.openai_agents import BraintrustTracingProcessor
from openai import AsyncOpenAI

from take_home.causal_chains.agents.chat_service.chat_service import (
    ChatService,
    format_sse,
)
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.clients.memcache.span_processor import (
    MemcacheSpanProcessor,
)
from take_home.causal_chains.agents.eval.offline.di.container import EvalContainer
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_config import RunConfig


def _openai_client(api_key: str) -> AsyncOpenAI:
    client = AsyncOpenAI(api_key=api_key)
    # AsyncOpenAI copies OPENAI_PROJECT_ID and OPENAI_ORG_ID when these are unset.
    # A stale shell project 401s with invalid_project. The key selects the account.
    client.project = None
    client.organization = None
    return client


def _trace_processors(memcache: Memcache) -> list[TracingProcessor]:
    processors: list[TracingProcessor] = [MemcacheSpanProcessor(memcache)]
    braintrust_api_key = os.environ.get("BRAINTRUST_API_KEY", "")
    project_id = os.environ.get("BRAINTRUST_PROJECT_ID", "")
    org_name = os.environ.get("BRAINTRUST_ORGANIZATION_NAME") or None
    if braintrust_api_key and project_id:
        logger = init_logger(
            project="causal_chains",
            project_id=project_id,
            api_key=braintrust_api_key,
            org_name=org_name,
        )
        processors.append(BraintrustTracingProcessor(logger))
    return processors


async def run_offline(
    query: str,
) -> tuple[ChatService, list[Message]]:
    container = EvalContainer()
    message_store = container.messaging_store()
    turn_store = container.turn_store()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    container.config.openai_api_key.from_value(api_key)
    if api_key:
        set_default_openai_client(_openai_client(api_key), use_for_tracing=False)
    set_trace_processors(_trace_processors(container.memcache()))
    service = container.chat_service()
    message = MarkdownMessage(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        text=query,
    )
    await message_store.append("1", message)
    turn = Turn(
        turn_id=f"t_{uuid.uuid4().hex[:8]}",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message=message.message_id,
    )
    await turn_store.put_turn(turn)
    messages = [
        item
        async for item in service.run_turn(
            turn,
            query,
            RunConfig(include_traces=True),
        )
    ]
    return service, messages


@click.command()
@click.option("--query", required=True)
def main(
    query: str,
) -> None:
    _service, messages = asyncio.run(run_offline(query))
    for message in messages:
        click.echo(format_sse(message), nl=False)


if __name__ == "__main__":
    main()
