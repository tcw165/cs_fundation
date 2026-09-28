from take_home.causal_chains.agents.models.messaging.sse_event import (
    RunTraces,
    SseDelta,
    SseDone,
    SseError,
    SseHeartbeat,
    SseTool,
)


def test_sse_delta_json():
    payload = SseDelta(text="oil ")
    assert payload.model_dump() == {"type": "delta", "text": "oil "}


def test_sse_tool_json():
    payload = SseTool(name="ground", status="called")
    assert payload.model_dump()["name"] == "ground"


def test_sse_done_json():
    assert SseDone(message_id="m_1").model_dump()["type"] == "done"


def test_sse_error_json():
    assert SseError(message="boom").message == "boom"


def test_run_traces_json():
    payload = RunTraces(text="span\n")
    assert payload.model_dump() == {"type": "run_traces", "text": "span\n"}


def test_sse_heartbeat_json():
    assert SseHeartbeat().model_dump() == {"type": "heartbeat"}
