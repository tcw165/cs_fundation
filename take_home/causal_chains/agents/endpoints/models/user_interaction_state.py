from pydantic import BaseModel, Field

from take_home.causal_chains.agents.endpoints.models.text_input_state import TextInputState
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState


DEFAULT_TEXT_INPUT_PLACEHOLDER = "Ask about a chain"


class UserInteractionState(BaseModel):
    text_input_state: TextInputState = Field(
        ...,
        description="Whether the reader can type, and whether a send can be stopped.",
    )
    text_input_placeholder: str = Field(
        default=DEFAULT_TEXT_INPUT_PLACEHOLDER,
        description="Placeholder text for the input field.",
    )
    thinking_state: ThinkingState | None = Field(
        default=None,
        description="Text shown while the assistant is thinking. Absent when it is not.",
    )
