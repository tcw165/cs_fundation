import os

import click
import uvicorn
from agents import add_trace_processor

from take_home.causal_chains.agents.clients.di.container import ClientsContainer
from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
def main(host: str, port: int) -> None:
    clients = ClientsContainer()
    add_trace_processor(clients.span_processor())
    container = AppContainer()
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    container.config.openai_api_key.from_value(openai_api_key)
    container.config.agent_runner.from_value("openai" if openai_api_key else "stub")
    container.check_dependencies()
    uvicorn.run(create_app(container), host=host, port=port)


if __name__ == "__main__":
    main()
