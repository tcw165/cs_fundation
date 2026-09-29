from pydantic import BaseModel, ConfigDict, Field

from take_home.causal_chains.agents.models.causal_chains.case import Case


class DeeplinkParam(BaseModel):
    """One query parameter on a deeplink."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Query parameter name.")
    value: str = Field(description="Query parameter value.")


class DeeplinkCard(BaseModel):
    """A chat card that opens one stored chain."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short name shown on the card.")
    subtitle: str = Field(description="One sentence under the title.")
    scheme: str = Field(description="URI scheme. Empty for an in-app path.")
    route: str = Field(
        description="In-app path. A stored chain is /chain/<case_id>. Do not include a version.",
    )
    params: list[DeeplinkParam] = Field(
        description=(
            "Query parameters as name and value pairs. "
            "Use an empty list for a stored chain."
        ),
    )


class DeeplinkRequest(BaseModel):
    """The case to open, and what the reader should see there."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

    deeplinks: list[DeeplinkCard]
