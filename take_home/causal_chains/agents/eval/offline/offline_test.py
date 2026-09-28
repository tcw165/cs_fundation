import asyncio
from types import SimpleNamespace

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
import take_home.causal_chains.agents.eval.offline.offline as offline_module
from take_home.causal_chains.agents.clients.memcache.span_processor import (
    MemcacheSpanProcessor,
)
from take_home.causal_chains.agents.eval.offline.offline import run_offline
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage
from take_home.causal_chains.agents.stores.causal_chain_store.graph_causal_chain_store import (
    GraphCausalChainStore,
)


def _silence_runner(monkeypatch) -> None:
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        lambda agent, input, context=None, max_turns=None: _fake_result(),
    )


class _FakeGraphDb:
    def __init__(self) -> None:
        self.cleared = False

    def clear(self) -> None:
        self.cleared = True


def test_offline_uses_the_graph_store_when_neo4j_uri_is_set(monkeypatch) -> None:
    seen: dict[str, object] = {}
    graph_db = _FakeGraphDb()

    def fake_build_graph_db(uri: str, user: str, password: str) -> _FakeGraphDb:
        seen["uri"] = uri
        seen["user"] = user
        seen["password"] = password
        return graph_db

    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "causal_chains")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_PROJECT_ID", raising=False)
    monkeypatch.setattr(offline_module, "build_graph_db", fake_build_graph_db)
    _silence_runner(monkeypatch)

    service, _events = asyncio.run(run_offline("hormuz"))
    store = service._causal_chain_store
    assert isinstance(store, GraphCausalChainStore)
    assert store._graph_db is graph_db
    assert graph_db.cleared is True
    assert seen == {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "causal_chains",
    }


def test_offline_skips_clear_when_clean_graph_is_off(monkeypatch) -> None:
    graph_db = _FakeGraphDb()
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_PROJECT_ID", raising=False)
    monkeypatch.setattr(offline_module, "build_graph_db", lambda uri, user, password: graph_db)
    _silence_runner(monkeypatch)

    asyncio.run(run_offline("hormuz", clean_graph=False))
    assert graph_db.cleared is False


def test_offline_does_not_clear_without_neo4j_uri(monkeypatch) -> None:
    called = {"build": False}

    def fake_build_graph_db(uri: str, user: str, password: str) -> _FakeGraphDb:
        called["build"] = True
        return _FakeGraphDb()

    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_PROJECT_ID", raising=False)
    monkeypatch.setattr(offline_module, "build_graph_db", fake_build_graph_db)
    _silence_runner(monkeypatch)

    asyncio.run(run_offline("hormuz"))
    assert called["build"] is False


def test_offline_keeps_the_decoy_store_without_neo4j_uri(monkeypatch) -> None:
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_PROJECT_ID", raising=False)
    _silence_runner(monkeypatch)

    service, _events = asyncio.run(run_offline("hormuz"))
    assert not isinstance(service._causal_chain_store, GraphCausalChainStore)


def test_offline_turn_saves_the_user_message_and_prints_runner_messages(
    monkeypatch,
) -> None:
    class _FakeDelta:
        def __init__(self, delta: str) -> None:
            self.delta = delta

    class _FakeResult:
        def stream_events(self):
            async def _events():
                yield SimpleNamespace(
                    type="raw_response_event",
                    data=_FakeDelta("one\n\ntwo"),
                )

            return _events()

        def cancel(self) -> None:
            return None

    seen_include_traces: list[bool] = []

    def run_streamed(
        agent,
        input,
        context=None,
        max_turns=None,
    ):
        seen_include_traces.append(context.run_config.include_traces)
        return _FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", _FakeDelta)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        run_streamed,
    )

    async def exercise():
        service, events = await run_offline("hormuz")
        messages = await service._messaging_store.list_messages("1")
        return messages, events

    messages, events = asyncio.run(exercise())
    user_messages = [message.text for message in messages if message.role == "user"]
    assert user_messages == ["hormuz"]
    assert [event.text for event in events] == ["one", "two"]
    assert all(isinstance(event, MarkdownMessage) for event in events)
    assert seen_include_traces == [True]


def test_offline_uses_the_api_key_without_a_shell_project(monkeypatch) -> None:
    installed: dict[str, object] = {}

    def capture_client(client: object, use_for_tracing: bool) -> None:
        installed["client"] = client
        installed["tracing"] = use_for_tracing

    def capture_processors(processors: list[object]) -> None:
        installed["processors"] = processors

    class _FakeResult:
        def stream_events(self):
            async def _events():
                if False:
                    yield None

            return _events()

        def cancel(self) -> None:
            return None

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj_stale")
    monkeypatch.setenv("OPENAI_ORG_ID", "org_stale")
    monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
    monkeypatch.delenv("BRAINTRUST_PROJECT_ID", raising=False)
    monkeypatch.setattr(offline_module, "set_default_openai_client", capture_client)
    monkeypatch.setattr(offline_module, "set_trace_processors", capture_processors)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        lambda agent, input, context=None, max_turns=None: _FakeResult(),
    )

    asyncio.run(run_offline("hormuz"))
    client = installed["client"]
    assert client.api_key == "sk-test"
    assert client.project is None
    assert client.organization is None
    assert installed["tracing"] is False
    processors = installed["processors"]
    assert isinstance(processors, list)
    assert len(processors) == 1
    assert isinstance(processors[0], MemcacheSpanProcessor)


def _fake_result():
    class _FakeResult:
        def stream_events(self):
            async def _events():
                if False:
                    yield None

            return _events()

        def cancel(self) -> None:
            return None

    return _FakeResult()


def test_offline_logs_to_braintrust_when_key_and_project_are_set(monkeypatch) -> None:
    inits: list[dict[str, object]] = []
    processor_lists: list[list[object]] = []

    def fake_init_logger(**kwargs: object) -> object:
        inits.append(kwargs)
        return object()

    monkeypatch.setenv("BRAINTRUST_API_KEY", "sk-test")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "proj_123")
    monkeypatch.setenv("BRAINTRUST_ORGANIZATION_NAME", "acme")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(offline_module, "init_logger", fake_init_logger)
    monkeypatch.setattr(
        offline_module,
        "BraintrustTracingProcessor",
        lambda logger: ("braintrust", logger),
    )
    monkeypatch.setattr(offline_module, "set_trace_processors", processor_lists.append)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        lambda agent, input, context=None, max_turns=None: _fake_result(),
    )

    asyncio.run(run_offline("hormuz"))
    assert inits == [
        {
            "project": "causal_chains",
            "project_id": "proj_123",
            "api_key": "sk-test",
            "org_name": "acme",
        }
    ]
    assert len(processor_lists) == 1
    processors = processor_lists[0]
    assert len(processors) == 2
    assert isinstance(processors[0], MemcacheSpanProcessor)
    assert processors[1][0] == "braintrust"


def test_offline_omits_braintrust_when_either_env_var_is_missing(monkeypatch) -> None:
    monkeypatch.delenv("BRAINTRUST_ORGANIZATION_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        lambda agent, input, context=None, max_turns=None: _fake_result(),
    )
    for api_key, project_id in (("", ""), ("sk-test", ""), ("", "proj_123")):
        processor_lists: list[list[object]] = []
        monkeypatch.setenv("BRAINTRUST_API_KEY", api_key)
        monkeypatch.setenv("BRAINTRUST_PROJECT_ID", project_id)
        monkeypatch.setattr(
            offline_module,
            "set_trace_processors",
            processor_lists.append,
        )
        asyncio.run(run_offline("hormuz"))
        assert len(processor_lists) == 1
        assert len(processor_lists[0]) == 1
        assert isinstance(processor_lists[0][0], MemcacheSpanProcessor)
