from enum import StrEnum

from take_home.causal_chains.agents.agents.path_builder.discovered_situations import (
    DiscoveredSituations,
    PathProgress,
)
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class DiscoveryAction(StrEnum):
    discover = "discover"
    close_out = "close_out"
    stop = "stop"


def situation_matches_ask(
    situation: Situation,
    user_ask: str,
) -> bool:
    return situation.desc.strip().casefold() == user_ask.strip().casefold()


def advance(
    found: DiscoveredSituations,
    user_ask: str,
) -> DiscoveryAction:
    if found.progress is PathProgress.closed:
        return DiscoveryAction.stop
    if any(
        situation_matches_ask(situation, user_ask) for situation in found.situations
    ):
        return DiscoveryAction.stop
    if found.progress is PathProgress.close:
        return DiscoveryAction.close_out
    return DiscoveryAction.discover


def path_prompt(
    user_ask: str,
    root_desc: str,
    action: DiscoveryAction,
) -> str:
    if action is DiscoveryAction.close_out:
        task = "The latest situations are close. Add the situations and links that close the path."
    else:
        task = "Add the next situations and the leads-to links."
    return f"User ask: {user_ask}\nNow: {root_desc}\n{task}"
