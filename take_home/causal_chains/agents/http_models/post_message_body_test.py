import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody


def test_post_message_body_parses():
    body = PostMessageBody(text="Hormuz opens")
    assert body.text == "Hormuz opens"


def test_post_message_body_accepts_text_inside_the_length_bounds():
    assert PostMessageBody(text="a").text == "a"
    assert PostMessageBody(text="a" * 9_999).text == "a" * 9_999


@pytest.mark.parametrize("text", ["", "a" * 10_000])
def test_post_message_body_rejects_text_outside_the_length_bounds(text: str):
    with pytest.raises(ValidationError):
        PostMessageBody(text=text)
