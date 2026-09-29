from pathlib import Path

from agents.agent_output import AgentOutputSchema

from take_home.causal_chains.agents.agents.deeplinks_finder.deeplinks_finder import (
    deeplinks_finder,
)
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkResult


def test_deeplinks_finder_returns_cards_for_the_case():
    prompt = (Path(__file__).parent / "prompts" / "deeplinks_finder.md").read_text()
    assert deeplinks_finder.instructions == prompt
    assert "# Goal" in prompt and "# Key Rules" in prompt
    assert "# Examples" not in prompt
    assert "Find the in-app destination for the case and the description." in prompt
    assert "The input is the case and the destination description." in prompt
    assert "route is `/chain/<case_id>`" in prompt
    assert "Take the case id from the case." in prompt
    assert "Do not include a version." in prompt
    assert "Do not write a story." in prompt
    assert deeplinks_finder.model == "gpt-5.6-luna"
    assert deeplinks_finder.output_type is DeeplinkResult
    assert deeplinks_finder.tools == []
    schema = AgentOutputSchema(DeeplinkResult).json_schema()
    assert schema["required"] == list(schema["properties"])
    params = schema["$defs"]["DeeplinkCard"]["properties"]["params"]
    assert params["type"] == "array"
    assert params["items"]["$ref"] == "#/$defs/DeeplinkParam"
    param = schema["$defs"]["DeeplinkParam"]
    assert param["required"] == list(param["properties"])
    assert set(param["properties"]) == {"name", "value"}
