from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MyBlog(BaseModel):
    kind: Literal["my_blog"] = Field(
        default="my_blog",
        description="The reader opened this from their blog.",
    )
    source_url: str = Field(
        ...,
        description="URL of the blog page that opened the conversation.",
    )
    source_ip: str = Field(..., description="IP address of the reader who opened it.")


EntryContext = Annotated[
    MyBlog,
    Field(discriminator="kind"),
]
