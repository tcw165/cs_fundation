from pathlib import Path

from agents import Agent, ModelSettings
from openai.types.shared.reasoning import Reasoning

from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkResult
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


deeplinks_finder = Agent[RunContext](
    name="deeplinks_finder",
    instructions=_read_prompt("deeplinks_finder.md"),
    model="gpt-5.6-luna",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="none"),
        verbosity="low",
    ),
    tools=[],
    output_type=DeeplinkResult,
)
