import asyncio
from types import SimpleNamespace
from uuid import UUID

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.agents.crystal_ball.examine import examine
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chain.event import Event
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext


def test_app_agent_runner_keeps_a_graph_only_when_the_score_rises(monkeypatch):
    class FakeDelta:
        def __init__(self, delta: str) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))
        yield SimpleNamespace(type="raw_response_event", data=object())

    rising = CausalChain()
    flat = CausalChain(
        events={
            UUID("11111111-1111-4111-8111-111111111111"): Event(
                event_id=UUID("11111111-1111-4111-8111-111111111111"),
                statement="later",
                depth=1,
                is_root=False,
            )
        }
    )
    chains = [rising, flat]
    prompts: list[str] = []
    seen: list[object] = []
    contexts: list[object] = []
    cache = InMemoryMemcache()

    class SeededEditor:
        def __init__(self, chain: CausalChain) -> None:
            self._chain = chain

        def get_chain(self) -> CausalChain:
            return self._chain

    class FakeResult:
        def __init__(self) -> None:
            self.final_output = None
            self.cancelled = False

        def stream_events(self):
            return fake_stream()

        def cancel(self):
            self.cancelled = True

    class FakeRunner:
        @staticmethod
        def run_streamed(agent, input, context=None):
            seen.append(agent)
            contexts.append(context)
            prompts.append(input)
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        run_config=RunConfig(include_traces=True),
    )

    async def collect():
        runner = AppAgentRunner(
            api_key="test",
            memcache=cache,
            editor_factory=lambda: SeededEditor(chains.pop(0)),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert contexts == [context, context]
    rising_exam = examine(rising)
    flat_exam = examine(flat)
    assert flat_exam.score <= rising_exam.score
    assert [agent.name for agent in seen] == ["crystal_ball", "crystal_ball"]
    assert prompts[0] == "hormuz"
    assert prompts[1] == f"hormuz\n{rising_exam.failures[0]}"
    scores = [event.text for event in events if event.type == "delta" and event.text.startswith("score ")]
    assert scores == [f"score {rising_exam.score}\n", f"score {flat_exam.score}\n"]
    graph_deltas = [event.text for event in events if event.type == "delta" and event.text.startswith("{")]
    assert graph_deltas == [rising.model_dump_json()]
    assert events[-2].type == "run_traces"
    assert events[-2].text == "span\nspan\n"
    assert cache.flush() == ""
    assert events[-1].type == "done"
    assert events[-1].message_id == "m_t_1"


def test_app_agent_runner_omits_run_traces_by_default(monkeypatch):
    class FakeDelta:
        def __init__(self, delta: str) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))

    cache = InMemoryMemcache()

    class FakeResult:
        final_output = "not a graph"

        def stream_events(self):
            return fake_stream()

        def cancel(self) -> None:
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(agent, input, context=None):
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        context = RunContext(conversation_id="1", turn_id="t_1")
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert all(event.type != "run_traces" for event in events)
    assert cache.flush() == ""
    assert events[-1].type == "done"
