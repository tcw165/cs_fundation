from take_home.causal_chains.agents.models.messaging.conversation import Conversation


def test_conversation_parses():
    conversation = Conversation(conversation_id="1")
    assert conversation.conversation_id == "1"
