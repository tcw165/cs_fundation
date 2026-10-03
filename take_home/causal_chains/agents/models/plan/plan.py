from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PlanStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    id: str = Field(..., description="Step id. Later steps point here.")
    goal: str = Field(..., description="What this step is for.")
    status: StepStatus = Field(
        default=StepStatus.PENDING,
        description="Pending until the step runs, succeeds, fails, or is skipped.",
    )
    next_on_success: str | None = Field(
        default=None,
        description="Step id to open when this step succeeds. Absent when the plan ends.",
    )
    next_on_failure: str | None = Field(
        default=None,
        description="Step id to open when this step fails. Absent when failure stops the plan.",
    )
    next_on_skip: str | None = Field(
        default=None,
        description="Step id to open when this step is skipped. Absent when a skip stops the plan.",
    )


class Plan(BaseModel):
    id: str = Field(..., description="Plan id.")
    status: PlanStatus = Field(
        ...,
        description="Whether the plan is pending, running, completed, or failed.",
    )
    steps: list[PlanStep] = Field(..., description="Steps in this plan.")
    created_at: datetime = Field(..., description="When the plan was created.")
    updated_at: datetime = Field(..., description="When the plan last changed.")
    message_count: int = Field(
        default=0,
        description="How many messages this plan has produced. Zero until that statistic is recorded.",
    )
