from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody


def test_post_message_body_parses():
    body = PostMessageBody(text="Hormuz opens")
    assert body.text == "Hormuz opens"
