from datetime import datetime, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from take_home.causal_chains.agents.models.messaging.protocol.revision import (
    Revision,
    RevisionRetracted,
    RevisionUpdated,
)

_adapter = TypeAdapter(Revision)
_at = datetime(2026, 9, 30, tzinfo=timezone.utc)


def test_retracted_revision_parses_without_content():
    revision = _adapter.validate_python({"kind": "revision_retracted", "at": _at})
    assert isinstance(revision, RevisionRetracted)
    assert revision.at == _at


def test_updated_revision_requires_content():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "revision_updated", "at": _at})
    revision = _adapter.validate_python(
        {"kind": "revision_updated", "at": _at, "content": "replaced"}
    )
    assert isinstance(revision, RevisionUpdated)
    assert revision.content == "replaced"


def test_missing_or_unknown_kind_does_not_parse():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"at": _at})
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "other", "at": _at})
