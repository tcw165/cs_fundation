from datetime import datetime, timezone

from agents import RunConfig
from agents.run_config import CallModelData, ModelInputData

from take_home.causal_chains.agents.agent_run_config.agent_run_config import (
    _decorate_tail_messages,
    decorate_tail_messages,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


def test_decorate_tail_messages_refreshes_the_clock_before_the_user():
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    data = CallModelData(
        model_data=ModelInputData(
            input=[
                {
                    "role": "assistant",
                    "content": (
                        "(this message is invisible to user)\n"
                        "Current time: 2020-01-01T00:00:00+00:00 UTC"
                    ),
                },
                {"role": "user", "content": "Future situation:\nopen"},
            ],
            instructions="stay",
        ),
        agent=object(),
        context=context,
    )
    updated = _decorate_tail_messages(data)
    assert updated.instructions == "stay"
    assert updated.input[0] == {
        "role": "assistant",
        "content": (
            "(this message is invisible to user)\n"
            "Current time: 2026-09-29T05:16:00+00:00 UTC"
        ),
    }
    assert updated.input[1]["role"] == "user"


def test_decorate_tail_messages_keeps_other_run_config_fields():
    existing = RunConfig(workflow_name="keep")
    updated = decorate_tail_messages(existing)
    assert updated.workflow_name == "keep"
    assert updated.call_model_input_filter is _decorate_tail_messages
    assert existing.call_model_input_filter is None
