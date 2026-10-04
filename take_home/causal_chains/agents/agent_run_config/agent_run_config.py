from dataclasses import replace
from datetime import datetime
from functools import cache
from pathlib import Path

from agents import RunConfig
from agents.run_config import CallModelData, ModelInputData

from take_home.causal_chains.agents.models.run_context import RunContext


@cache
def _read_template(name: str) -> str:
    path = Path(__file__).parent / "templates" / name
    return path.read_text().rstrip("\n")


def make_current_time_reminder_message(moment: datetime) -> dict[str, str]:
    content = (
        _read_template("current_time.md")
        .replace("{current_time_iso_format}", moment.isoformat())
        .replace("{timezone_name}", moment.tzname() or "")
    )
    return {"role": "assistant", "content": content}


def _decorate_tail_messages(data: CallModelData[RunContext]) -> ModelInputData:
    note = make_current_time_reminder_message(data.context.clock.now())
    items = list(data.model_data.input)
    user_at = next(
        index
        for index in range(len(items) - 1, -1, -1)
        if items[index].get("role") == "user"
    )
    previous = user_at - 1
    if (
        previous >= 0
        and items[previous].get("role") == "assistant"
        and str(items[previous].get("content", "")).startswith(
            "(this message is invisible to user)"
        )
    ):
        items[previous] = note
    else:
        items.insert(user_at, note)
    return ModelInputData(input=items, instructions=data.model_data.instructions)


def decorate_tail_messages(run_config: RunConfig | None = None) -> RunConfig:
    """Attach the current-time note to every model call of this run.

    A nested run, or an agent used as a tool, replaces the parent RunConfig
    when it passes its own. The note lives only on call_model_input_filter,
    so that replacement drops the clock and the model cannot tell how old a
    message is. Pass a config you already built to keep its other settings.
    Omit it to get a config that only carries the note.
    """
    note_filter = _decorate_tail_messages
    if run_config is None:
        return RunConfig(call_model_input_filter=note_filter)
    return replace(run_config, call_model_input_filter=note_filter)
