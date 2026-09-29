from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.causal_chains.case import Case


class DeeplinkCard(BaseModel):
    """A chat card that opens one stored chain."""

    title: str = Field(description="Short name shown on the card.")
    subtitle: str = Field(description="One sentence under the title.")
    scheme: str = Field(description="URI scheme. Empty for an in-app path.")
    route: str = Field(
        description="In-app path. A stored chain is /chain/<case_id>. Do not include a version.",
    )
    params: dict[str, str] = Field(
        description="Query parameters. Empty for a stored chain.",
    )


class DeeplinkRequest(BaseModel):
    """The case to open, and what the reader should see there."""

    case: Case = Field(
        description=(
            "The current case. The route uses this case id. Do not invent a case id."
        ),
    )
    destination_desc: str = Field(
        description=(
            "What the reader should open on that case. Do not include a version."
        ),
    )


class DeeplinkResult(BaseModel):
    """Cards for that destination."""

    deeplinks: list[DeeplinkCard]
