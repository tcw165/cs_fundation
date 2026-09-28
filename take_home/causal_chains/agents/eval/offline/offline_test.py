import asyncio

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.eval.offline.offline import run_offline


def test_offline_turn_saves_the_user_message_and_emits_done(
    monkeypatch,
) -> None:
    class _FakeResult:
        def stream_events(self):
            async def _events():
                if False:
                    yield None

            return _events()

        def cancel(self) -> None:
            return None

    def run_streamed(
        agent,
        input,
        context=None,
    ):
        return _FakeResult()

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
    assert any(event.type == "done" for event in events)
