import asyncio
from types import SimpleNamespace

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.eval.offline.offline import run_offline
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage


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
