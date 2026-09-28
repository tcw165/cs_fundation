from pathlib import Path

from agents import Agent, ModelSettings, ToolsToFinalOutputResult
from agents.tool import FunctionToolResult

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
    make_deeplink_widget,
    return_root,
)
from take_home.causal_chains.agents.agents.now_scout.now_scout import now_scout
from take_home.causal_chains.agents.agents.path_builder.path_builder import path_builder
from take_home.causal_chains.agents.agents.pricer.pricer import pricer
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_context import RunContext


def _stop_when_root_returned(
    _context: object,
    tool_results: list[FunctionToolResult],
) -> ToolsToFinalOutputResult:
    for tool_result in tool_results:
        if tool_result.tool.name == "return_root" and isinstance(
            tool_result.output,
            Situation,
        ):
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=tool_result.output,
            )
    return ToolsToFinalOutputResult(is_final_output=False, final_output=None)


def _read_prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text()


causal_chain = Agent[RunContext](
    name="causal_chain",
    instructions=_read_prompt("causal_chain.md"),
    model="gpt-5.6-luna",
    tools=[
        now_scout.as_tool(
            tool_name="now_scout",
            tool_description=(
                "Save the present and return that situation, including its id."
            ),
        ),
        path_builder.as_tool(
            tool_name="path_builder",
            tool_description=(
                "Save the next situations from the current description "
                "and the thoughts about remaining attempts, and return them."
            ),
        ),
        pricer.as_tool(
            tool_name="pricer",
            tool_description=(
                "Name the input variables on the link from the current situation "
                "to one next situation."
            ),
        ),
        add_situation,
        link_situations,
        make_deeplink_widget,
        return_root,
    ],
    model_settings=ModelSettings(tool_choice="required"),
    tool_use_behavior=_stop_when_root_returned,
)
