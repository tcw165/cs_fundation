from collections.abc import Coroutine
from typing import Any
from uuid import UUID

from decoy import Decoy, matchers

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
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
    messages: list[Message] = []
    turns: dict[str, Turn] = {}
    situations: dict[UUID, Situation] = {}
    links: list[LeadsTo] = []

    def remember_message(
        message: Message,
    ) -> None:
        messages.append(message)

    def list_messages(
        conversation_id: str,
    ) -> list[Message]:
        return [
            message
            for message in messages
            if message.conversation_id == conversation_id
        ]

    def remember_turn(
        turn: Turn,
    ) -> None:
        turns[turn.turn_id] = turn

    def load_turn(
        turn_id: str,
    ) -> Turn | None:
        return turns.get(turn_id)

    def remember_situation(
        situation: Situation,
    ) -> None:
        situations[situation.situation_id] = situation

    def remember_link(
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        remember_situation(from_situation)
        remember_situation(to_situation)
        links.append(link)

    def load_chains() -> list[CausalChain]:
        stored = list(situations.values())
        root_count = sum(1 for situation in stored if situation.is_root)
        if root_count != 1:
            return []
        return [
            CausalChain(
                situations=stored,
                links=list(links),
            )
        ]

    decoy.when(
        _drive(messaging_store.append(matchers.Anything())),
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
        _drive(causal_chain_store.add_situation(matchers.Anything())),
        ignore_extra_args=True,
    ).then_do(remember_situation)
    decoy.when(
        _drive(
            causal_chain_store.link_situations(
                matchers.Anything(),
                matchers.Anything(),
                matchers.Anything(),
            )
        ),
        ignore_extra_args=True,
    ).then_do(remember_link)
    decoy.when(
        _drive(causal_chain_store.get_chains()),
    ).then_do(load_chains)
