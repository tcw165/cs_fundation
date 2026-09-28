import asyncio
import os
import uuid

import click

from take_home.causal_chains.agents.chat_service.chat_service import (
    ChatService,
    format_sse,
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


async def run_offline(
    query: str,
) -> tuple[ChatService, list[Message]]:
    container = EvalContainer()
    container.config.openai_api_key.from_value(os.environ.get("OPENAI_API_KEY", ""))
    service = container.chat_service()
    message = MarkdownMessage(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        text=query,
    )
    await container.messaging_store().append("1", message)
    turn = Turn(
        turn_id=f"t_{uuid.uuid4().hex[:8]}",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message=message.message_id,
    )
    await container.turn_store().put_turn(turn)
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
