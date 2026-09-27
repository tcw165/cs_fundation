from uuid import UUID

from take_home.causal_chains.agents.agents.crystal_ball.discover import (
    DiscoveryAction,
    advance,
    path_prompt,
)
from take_home.causal_chains.agents.agents.path_builder.discovered_situations import (
    DiscoveredSituations,
    PathProgress,
)
from take_home.causal_chains.agents.models.causal_chains.situation import Situation

ASK = "The Strait of Hormuz is going to open next week."
NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


def _found(
    progress: PathProgress,
    desc: str,
) -> DiscoveredSituations:
    return DiscoveredSituations(
        situations=[Situation(situation_id=NOW_ID, desc=desc, is_root=False)],
        progress=progress,
    )


def test_closed_progress_stops():
    assert advance(_found(PathProgress.closed, "still shut"), ASK) is DiscoveryAction.stop


def test_matching_desc_stops_even_when_far():
    assert advance(_found(PathProgress.far, f"  {ASK.upper()}  "), ASK) is DiscoveryAction.stop


def test_close_asks_for_a_close_out():
    assert advance(_found(PathProgress.close, "a deal this week"), ASK) is DiscoveryAction.close_out


def test_far_keeps_discovering():
    assert advance(_found(PathProgress.far, "talks stall"), ASK) is DiscoveryAction.discover


def test_close_out_prompt_asks_to_close_the_path():
    text = path_prompt(ASK, "strait shut", DiscoveryAction.close_out)
    assert "close the path" in text
    assert ASK in text
    assert "strait shut" in text
