import pytest
from pydantic import TypeAdapter, ValidationError

from take_home.causal_chains.agents.models.messaging.followup_question import (
    FollowupQuestion,
    TextFollowupQuestion,
    UriFollowupQuestion,
)

_adapter = TypeAdapter(FollowupQuestion)


def test_text_question_parses_with_only_content():
    question = _adapter.validate_python(
        {"kind": "text_followup_question", "content": "What happens next?"}
    )
    assert isinstance(question, TextFollowupQuestion)
    assert question.content == "What happens next?"


def test_uri_question_requires_preview_and_source_uri():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "uri_followup_question", "preview": "Open"})
    question = _adapter.validate_python(
        {
            "kind": "uri_followup_question",
            "preview": "Open",
            "source_uri": "https://example.com/post",
        }
    )
    assert isinstance(question, UriFollowupQuestion)
    assert question.source_uri == "https://example.com/post"


def test_missing_or_unknown_kind_does_not_parse():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"content": "What happens next?"})
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "other", "content": "What happens next?"})
