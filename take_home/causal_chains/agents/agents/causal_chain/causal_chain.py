from pathlib import Path

from agents import Agent, ModelSettings
from openai.types.shared.reasoning import Reasoning

from take_home.causal_chains.agents.agent_run_config.agent_run_config import (
    decorate_tail_messages,
)
from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_case,
    add_terminal_situation,
    get_case,
    lookup_chain_so_far,
    reaches_terminal,
)
from take_home.causal_chains.agents.agent_tools.widgets import show_deeplink_widget
from take_home.causal_chains.agents.agents.deeplinks_finder.deeplinks_finder import (
    deeplinks_finder,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.models.causal_chains.now_scout_models import (
    NowScoutRequest,
)
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkRequest
from take_home.causal_chains.agents.models.causal_chains.path_builder_models import (
    PathBuilderRequest,
)
from take_home.causal_chains.agents.models.run_context import RunContext


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


causal_chain = Agent[RunContext](
    name="causal_chain",
    instructions=_read_prompt("causal_chain.md"),
    model="gpt-5.6-luna",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),
        verbosity="low",
    ),
    tools=[
        add_case,
        get_case,
        now_scout.as_tool(
            tool_name="now_scout",
            tool_description=(
                "Find the present. Use this once, after the case exists. "
                "Pass that case and the future you were given. "
                "It comes back saved as the start."
            ),
            parameters=NowScoutRequest,
            run_config=decorate_tail_messages(),
        ),
        add_terminal_situation,
        reaches_terminal,
        lookup_chain_so_far,
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Take one step from the current situation toward the future. "
                "Use this after both ends exist, and again until a path runs from the start to the future. "
                "Pass the current situation, the saved future, and a direction. "
                "The direction starts with the case id, then the open line, then the one driver to change. "
                "That driver comes from the start, and this line has not already changed it. "
                "Either link the current situation to the terminal, "
                "or save one next situation and link the current situation to it."
            ),
            parameters=PathBuilderRequest,
            run_config=decorate_tail_messages(),
        ),
        deeplinks_finder.as_tool(
            tool_name="deeplinks_finder",
            tool_description=(
                "Find the in-app destination for the case and the description. "
                "The input is the case and the destination description. "
                "Return one card when it names one stored chain. "
                "title is a short name. subtitle is one sentence. "
                "Scheme is always causal_chains. For a stored chain, route is /chain/<case_id>, and params is empty. "
                "Take the case id from the case. Do not invent a case id. Do not include a version. "
                "Do not save anything. Do not write a story."
            ),
            parameters=DeeplinkRequest,
            run_config=decorate_tail_messages(),
        ),
        show_deeplink_widget,
    ],
    output_type=str,
)
