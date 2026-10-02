from collections.abc import Coroutine
from datetime import datetime
from typing import Any
from uuid import UUID

from decoy import Decoy, matchers

from take_home.causal_chains.agents.constants.graph import LEADS_TO_HOP_LIMIT
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import (
    ChainSoFar,
    LinkedHop,
)
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore


def _drive(
    call: Coroutine[Any, Any, Any],
) -> None:
    try:
        call.send(None)
    except StopIteration:
        return


def rehearse_persistence(
    decoy: Decoy,
    messaging_store: MessagingStore,
    turn_store: TurnStore,
    causal_chain_store: CausalChainStore,
) -> None:
    messages: list[tuple[str, Message]] = []
    turns: dict[str, Turn] = {}
    cases: dict[UUID, Case] = {}
    situations: dict[UUID, tuple[Case, Situation]] = {}
    links: list[tuple[Case, LeadsTo]] = []

    def remember_message(
        conversation_id: str,
        message: Message,
    ) -> None:
        messages.append((conversation_id, message))

    def list_messages(
        conversation_id: str,
        limit: int,
        after_message: str | None = None,
        after_message_timestamp: datetime | None = None,
    ) -> MessagePage:
        matched = [
            message
            for stored_id, message in messages
            if stored_id == conversation_id
        ]
        if after_message is not None:
            start = next(
                (
                    index + 1
                    for index, message in enumerate(matched)
                    if message.message_id == after_message
                ),
                None,
            )
            if start is None:
                return MessagePage(messages=[])
            matched = matched[start:]
        page = matched[:limit]
        next_cursor = page[-1].message_id if len(page) == limit else None
        return MessagePage(messages=page, next_cursor=next_cursor)

    def remember_turn(
        turn: Turn,
    ) -> None:
        turns[turn.turn_id] = turn

    def load_turn(
        turn_id: str,
    ) -> Turn | None:
        return turns.get(turn_id)

    def remember_case(
        case: Case,
    ) -> None:
        cases[case.case_id] = case

    def load_case(
        case_id: UUID,
    ) -> Case:
        case = cases.get(case_id)
        if case is None:
            raise ValueError("case is missing")
        return case

    def remember_situation(
        case: Case,
        situation: Situation,
    ) -> None:
        situations[situation.situation_id] = (case, situation)

    def remember_link(
        case: Case,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        remember_situation(case, from_situation)
        remember_situation(case, to_situation)
        links.append((case, link))

    def load_leaves(
        case: Case,
        start: StartSituation,
    ) -> list[Situation]:
        return []

    def load_reaches(
        case: Case,
        start: StartSituation,
        terminal: Situation,
    ) -> bool:
        outgoing: dict[tuple[UUID, int], list[tuple[UUID, int]]] = {}
        for stored_case, link in links:
            if stored_case.case_id != case.case_id:
                continue
            key = (link.from_situation_id, link.from_version)
            outgoing.setdefault(key, []).append(
                (link.to_situation_id, link.to_version)
            )
        goal = (terminal.situation_id, terminal.version)
        seen: set[tuple[UUID, int]] = set()
        frontier = [(start.situation_id, start.version)]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            if current == goal:
                return True
            seen.add(current)
            frontier.extend(outgoing.get(current, []))
        return False

    def load_chain_so_far(
        case: Case,
        start: StartSituation,
    ) -> ChainSoFar:
        outgoing: dict[tuple[UUID, int], list[LeadsTo]] = {}
        for stored_case, link in links:
            if stored_case.case_id != case.case_id:
                continue
            key = (link.from_situation_id, link.from_version)
            outgoing.setdefault(key, []).append(link)
        hops: list[LinkedHop] = []
        current = (start.situation_id, start.version)
        seen: set[tuple[UUID, int]] = set()
        while len(hops) < LEADS_TO_HOP_LIMIT:
            if current in seen:
                break
            seen.add(current)
            candidates: list[tuple[Situation, LeadsTo]] = []
            for link in outgoing.get(current, []):
                stored = situations.get(link.to_situation_id)
                if stored is None:
                    continue
                stored_case, dest = stored
                if stored_case.case_id != case.case_id:
                    continue
                if isinstance(dest, TerminalSituation) or type(dest) is not Situation:
                    continue
                candidates.append((dest, link))
            if len(candidates) != 1:
                break
            dest, link = candidates[0]
            hops.append(LinkedHop(situation=dest, link=link))
            current = (dest.situation_id, dest.version)
        return ChainSoFar(start=start, hops=hops)

    def load_chains() -> list[CausalChain]:
        grouped: dict[UUID, list[Situation]] = {}
        for case, situation in situations.values():
            grouped.setdefault(case.case_id, []).append(situation)
        chains: list[CausalChain] = []
        for case_id, stored in grouped.items():
            start_count = sum(
                1 for situation in stored if isinstance(situation, StartSituation)
            )
            if start_count != 1:
                continue
            case_links = [
                link
                for case, link in links
                if case.case_id == case_id
            ]
            chains.append(
                CausalChain(
                    situations=stored,
                    links=case_links,
                )
            )
        return chains

    decoy.when(
        _drive(
            messaging_store.append(
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(remember_message)
    decoy.when(
        _drive(messaging_store.list_messages(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(list_messages)
    decoy.when(
        _drive(turn_store.put_turn(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(remember_turn)
    decoy.when(
        _drive(turn_store.get_turn(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(load_turn)
    decoy.when(
        _drive(causal_chain_store.add_case(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(remember_case)
    decoy.when(
        _drive(causal_chain_store.get_case(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(load_case)
    decoy.when(
        _drive(
            causal_chain_store.add_situation(
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(remember_situation)
    decoy.when(
        _drive(
            causal_chain_store.link_situations(
                matchers.Anything(),
                matchers.Anything(),
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(remember_link)
    decoy.when(
        _drive(
            causal_chain_store.lookup_leaf_situations(
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(load_leaves)
    decoy.when(
        _drive(
            causal_chain_store.reaches_terminal(
                matchers.Anything(),
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(load_reaches)
    decoy.when(
        _drive(
            causal_chain_store.lookup_chain_so_far(
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(load_chain_so_far)
    decoy.when(
        _drive(causal_chain_store.get_chains()),
    ).then_do(load_chains)
