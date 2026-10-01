import pytest
from pydantic import TypeAdapter, ValidationError

from take_home.causal_chains.agents.models.messaging.entry_context import EntryContext, MyBlog

_adapter = TypeAdapter(EntryContext)


def test_my_blog_requires_source_url_and_source_ip():
    with pytest.raises(ValidationError):
        MyBlog(source_url="https://example.com/post")
    blog = MyBlog(source_url="https://example.com/post", source_ip="203.0.113.4")
    assert blog.kind == "my_blog"
    parsed = _adapter.validate_python(blog.model_dump())
    assert isinstance(parsed, MyBlog)


def test_unknown_kind_does_not_parse():
    with pytest.raises(ValidationError):
        _adapter.validate_python(
            {
                "kind": "other",
                "source_url": "https://example.com/post",
                "source_ip": "203.0.113.4",
            }
        )
