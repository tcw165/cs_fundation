import asyncio
from types import SimpleNamespace

from take_home.causal_chains.agents.openai_runner.openai_turn_runner import OpenaiTurnRunner
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


def test_openai_turn_runner_maps_fake_stream(monkeypatch):
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

    monkeypatch.setattr(
        "take_home.causal_chains.agents.openai_runner.openai_turn_runner.ResponseTextDeltaEvent",
        FakeDelta,
        raising=False,
    )

    import take_home.causal_chains.agents.openai_runner.openai_turn_runner as module

    monkeypatch.setattr(module, "Agent", lambda **kwargs: object(), raising=False)

    async def run_with_patched_import():
        runner = OpenaiTurnRunner(api_key="test")

        async def patched_run(turn, text):
            result = FakeResult()
            from take_home.causal_chains.models.sse_event import SseDelta, SseDone

            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, FakeDelta):
                    yield SseDelta(text=event.data.delta)
            yield SseDone(message_id=f"m_{turn.turn_id}")

        runner.run = patched_run  # type: ignore[method-assign]
        turn = Turn(turn_id="t_1", conversation_id="1", status=TurnStatus.queued)
        return [event async for event in runner.run(turn, "hormuz")]

    events = asyncio.run(run_with_patched_import())
    assert events[0].type == "delta"
    assert events[0].text == "oil "
    assert events[-1].type == "done"
