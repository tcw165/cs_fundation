import asyncio
import os

import click

from take_home.causal_chains.agents.chat_service.chat_service import (
    ChatService,
    format_sse,
)
from take_home.causal_chains.agents.eval.offline.di.container import EvalContainer
from take_home.causal_chains.agents.models.messaging.sse_event import SseEvent
from take_home.causal_chains.agents.models.run_config import RunConfig


async def run_offline(
    query: str,
) -> tuple[ChatService, list[SseEvent]]:
    container = EvalContainer()
    container.config.openai_api_key.from_value(os.environ.get("OPENAI_API_KEY", ""))
    service = container.chat_service()
    turn = await service.post_message("1", query)
    context = service._contexts[turn.turn_id]
    context.run_config = RunConfig(include_traces=True)
    await service.run_turn(turn, query)
    return service, list(service._buffers[turn.turn_id])


@click.command()
@click.option("--query", required=True)
def main(
    query: str,
) -> None:
    _service, events = asyncio.run(run_offline(query))
    for event in events:
        click.echo(format_sse(event), nl=False)


if __name__ == "__main__":
    main()
