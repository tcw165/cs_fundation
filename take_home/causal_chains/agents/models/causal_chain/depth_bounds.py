from pydantic import BaseModel, model_validator


class DepthBounds(BaseModel):
    """Hop limits for one run.

    min_depth is the shortest path that may count as a destination.
    max_depth is the deepest event the editor will accept. The model does
    not choose these numbers.
    """

    min_depth: int = 2
    max_depth: int = 4

    @model_validator(mode="after")
    def max_covers_min(self) -> "DepthBounds":
        if self.min_depth < 1 or self.max_depth < self.min_depth:
            raise ValueError("depth bounds are invalid")
        return self
