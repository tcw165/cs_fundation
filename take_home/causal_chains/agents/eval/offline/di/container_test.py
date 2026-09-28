import inspect

from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.eval.offline.di import container as container_module
from take_home.causal_chains.agents.eval.offline.di.container import EvalContainer
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


def test_eval_container_wires_the_real_runner_to_store_mocks() -> None:
    container = EvalContainer()
    container.config.openai_api_key.from_value("test-key")
    runner = container.app_agent_runner()
    store = container.causal_chain_store()
    service = container.chat_service()
    source = inspect.getsource(container_module)

    assert isinstance(runner, AppAgentRunner)
    assert container.app_agent_runner() is runner
    assert isinstance(store, CausalChainStore)
    assert isinstance(service, ChatService)
    assert service._agent_runner is runner
    assert "boto3" not in source
    assert "neo4j" not in source
