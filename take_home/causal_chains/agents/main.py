import os

import click
import uvicorn
from agents import set_trace_processors
from braintrust import init_logger
from braintrust.integrations.openai_agents import BraintrustTracingProcessor

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app
from take_home.causal_chains.agents.observability.endpoint_logging.endpoint_logging import (
    silence_some_endpoints_log,
)


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
def main(host: str, port: int) -> None:
    container = AppContainer()
    processors = [container.clients().span_processor()]
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
    set_trace_processors(processors)
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    container.config.openai_api_key.from_value(openai_api_key)
    container.config.user_uuid.from_value("user-1")
    container.config.agent_runner.from_value("openai" if openai_api_key else "stub")
    container.check_dependencies()
    silence_some_endpoints_log()
    uvicorn.run(create_app(container), host=host, port=port)


if __name__ == "__main__":
    main()
