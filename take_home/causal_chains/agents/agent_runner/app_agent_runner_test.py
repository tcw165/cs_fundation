import asyncio
from types import SimpleNamespace

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.models.runner_context import RunnerContext


def test_app_agent_runner_maps_fake_stream(monkeypatch):
    class FakeDelta:
        def __init__(self, delta: str) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))
        yield SimpleNamespace(type="raw_response_event", data=object())

    class FakeResult:
        def stream_events(self):
            return fake_stream()

        def cancel(self):
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(agent, input):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Agent", lambda **kwargs: object())
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test")
        context = RunnerContext(conversation_id="1", turn_id="t_1")
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert events[0].type == "delta"
    assert events[0].text == "oil "
    assert events[-1].type == "done"
    assert events[-1].message_id == "m_t_1"
