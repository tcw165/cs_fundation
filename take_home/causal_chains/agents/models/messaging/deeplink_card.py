from uuid import UUID

from pydantic import BaseModel


class DeeplinkCard(BaseModel):
    """A chat card that opens one stored chain."""

    title: str
    root_situation_id: UUID
    root_version: int
