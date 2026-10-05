from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class GraphDb(Protocol):
    def p_query(self, destination_ids: list[UUID]) -> Decimal:
        """Sum the path probabilities from the start to those destination ids.

        Returns that probability.
        """
        ...

    def start_count(self) -> int:
        """Count the stored start situations.

        Returns the count.
        """
        ...

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]:
        """Find situations whose outgoing link probabilities do not sum to 1.

        Returns each situation id and that sum.
        """
        ...

    def merge_case(
        self,
        case_id: UUID,
        conversation_id: str,
        from_message_id: str,
        created_timestamp: str,
        updated_timestamp: str,
    ) -> None:
        """Save a case. Returns nothing."""
        ...

    def get_case(self, case_id: UUID) -> tuple[UUID, str, str, str, str] | None:
        """Load one case by the id assigned when it was created.

        Returns the case id, conversation id, creating message id, created time,
        and updated time. None means the case is missing.
        """
        ...

    def lookup_situation(
        self,
        situation_id: UUID,
    ) -> tuple[
        tuple[UUID, int, str, str, str, list[str], str],
        tuple[UUID, int, str, str, str, list[str], str],
        tuple[UUID, int, str, str, str, list[str], str],
    ] | None:
        """Load the situation for that id, the parent that leads to it, and the terminal on its case.

        Returns that situation, its parent, and the terminal. Each value is the id,
        version, created time, title, description, remained drivers, and kind.
        None means the situation is missing, it has no single parent, or the case
        does not have one terminal.
        """
        ...

    def list_latest_cases(
        self,
        conversation_id: str,
        limit: int,
    ) -> list[tuple[UUID, str, str, str, str]]:
        """Load the newest cases in a conversation.

        Returns each case id, conversation id, creating message id, created time,
        and updated time, newest first, up to the limit.
        """
        ...

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        created_timestamp: str,
        title: str,
        desc: str,
        remained_drivers: list[str],
        case_id: UUID,
        kind: str,
    ) -> None:
        """Save a situation on a case. Returns nothing."""
        ...

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, str, float]],
    ) -> None:
        """Save the leads-to link between two situations. Returns nothing."""
        ...

    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, str, str, list[str], str, UUID]]:
        """Load every stored situation.

        Returns each situation id, version, created time, title, description,
        remained drivers, kind, and the case id it belongs to.
        """
        ...

    def list_leaf_situations(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> list[tuple[UUID, int, str, str, str, list[str]]]:
        """Load mid-chain situations reached from the start that have no outgoing link.

        Returns each situation id, version, created time, title, description,
        and remained drivers.
        """
        ...

    def reaches_terminal(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
        terminal_situation_id: UUID,
        terminal_version: int,
    ) -> bool:
        """Validate whether the start situation connects to the terminal situation.

        Returns true when a path runs from that start to that terminal.
        """
        ...

    def lookup_chain_so_far(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> tuple[
        tuple[UUID, int, str, str, str, list[str]],
        list[tuple[UUID, int, str, str, str, list[str]]],
        list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]],
    ] | None:
        """Load the open line from the start through the current situation.

        Returns the start, the hops, and the links. The terminal is not included.
        None means the start is missing.
        """
        ...

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]]:
        """Load every leads-to link.

        Returns each from id, from version, to id, to version, probability, and inputs.
        """
        ...

    def clear(self) -> None:
        """Delete the stored situations. Returns nothing."""
        ...
