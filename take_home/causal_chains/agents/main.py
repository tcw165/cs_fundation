import os

import click
import uvicorn

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
def main(host: str, port: int) -> None:
    container = AppContainer()
    container.config.database_url.from_env(
        "DATABASE_URL",
        default="postgresql://causal_chains:causal_chains@db:5432/causal_chains",
    )
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    container.config.openai_api_key.from_value(openai_api_key)
    container.config.turn_runner.from_value("openai" if openai_api_key else "stub")
    container.check_dependencies()
    uvicorn.run(create_app(container), host=host, port=port)


if __name__ == "__main__":
    main()
