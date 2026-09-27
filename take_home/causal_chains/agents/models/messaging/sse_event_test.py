from take_home.causal_chains.agents.models.messaging.sse_event import (
    SseDelta,
    SseDone,
    SseError,
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
