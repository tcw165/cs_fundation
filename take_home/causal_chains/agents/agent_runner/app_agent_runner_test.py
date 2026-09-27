import asyncio
from types import SimpleNamespace
from uuid import UUID

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.discovered_situations import (
    DiscoveredSituations,
    PathProgress,
)
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
ASK = "The Strait of Hormuz is going to open next week."


class _Store:
    def __init__(self) -> None:
        self.situations: list[Situation] = []

    async def add_situation(
        self,
        situation: Situation,
    ) -> None:
        self.situations.append(situation)


def _situation(
    situation_id: UUID,
    desc: str,
    is_root: bool,
) -> Situation:
    return Situation(situation_id=situation_id, desc=desc, is_root=is_root)


def _found(
    desc: str,
    progress: PathProgress,
) -> DiscoveredSituations:
    return DiscoveredSituations(
        situations=[_situation(DEAL_ID, desc, False)],
        progress=progress,
    )


def _install_runner(
    monkeypatch,
    outputs: list[object],
    cache: InMemoryMemcache,
) -> list[tuple[object, str]]:
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))

    calls: list[tuple[object, str]] = []

    class FakeResult:
        def __init__(
            self,
            output: object,
        ) -> None:
            self.final_output = output
            self.cancelled = False

        def stream_events(self):
            return fake_stream()

        def cancel(self) -> None:
            self.cancelled = True

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
        ):
            calls.append((agent, input))
            cache.append("span\n")
            return FakeResult(outputs[len(calls) - 1])

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)
    return calls


def _run(
    monkeypatch,
    outputs: list[object],
    quota: int,
    include_traces: bool = False,
) -> tuple[list[object], list[tuple[object, str]], _Store]:
    cache = InMemoryMemcache()
    calls = _install_runner(monkeypatch, outputs, cache)
    store = _Store()
    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        run_config=RunConfig(
            include_traces=include_traces,
            attempt_quota=quota,
        ),
        clients=RunClients(causal_chain_store=store),
    )

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        return [event async for event in runner.stream([ASK], context)]

    events = asyncio.run(collect())
    return events, calls, store


def test_app_agent_runner_stops_when_the_path_closes(monkeypatch):
    root = _situation(NOW_ID, "strait shut", True)
    events, calls, store = _run(
        monkeypatch,
        [
            root,
            _found("talks stall", PathProgress.far),
            _found("a deal this week", PathProgress.close),
            _found("ships move", PathProgress.closed),
        ],
        quota=6,
        include_traces=True,
    )
    agents = [agent for agent, _prompt in calls]
    prompts = [prompt for _agent, prompt in calls]
    assert agents == [now_scout, path_builder, path_builder, path_builder]
    assert prompts[0] == ASK
    assert "Add the next situations" in prompts[1]
    assert "close the path" in prompts[3]
    assert store.situations == [root]
    deltas = [event.text for event in events if event.type == "delta"]
    assert deltas == ["oil ", "oil ", "oil ", "oil "]
    assert events[-2].type == "run_traces"
    assert events[-2].text == "span\nspan\nspan\nspan\n"
    assert events[-1].type == "done"
    assert events[-1].message_id == "m_t_1"


def test_matching_situation_stops_before_the_quota(monkeypatch):
    root = _situation(NOW_ID, "strait shut", True)
    _events, calls, _store = _run(
        monkeypatch,
        [root, _found(ASK, PathProgress.far)],
        quota=4,
    )
    assert [agent for agent, _prompt in calls] == [now_scout, path_builder]


def test_close_on_the_last_attempt_does_not_exceed_the_quota(monkeypatch):
    root = _situation(NOW_ID, "strait shut", True)
    _events, calls, _store = _run(
        monkeypatch,
        [root, _found("a deal this week", PathProgress.close)],
        quota=1,
    )
    assert len(calls) == 2
    assert "close the path" not in calls[1][1]


def test_app_agent_runner_omits_run_traces_by_default(monkeypatch):
    root = _situation(NOW_ID, "strait shut", True)
    events, _calls, _store = _run(
        monkeypatch,
        [root, _found("ships move", PathProgress.closed)],
        quota=2,
    )
    assert all(event.type != "run_traces" for event in events)
    assert events[-1].type == "done"
