from datetime import datetime, timezone

from take_home.causal_chains.agents.models.messaging.plan import Plan, PlanStatus, PlanStep, StepStatus


def test_step_defaults_to_pending():
    step = PlanStep(id="s1", goal="Open the strait")
    assert step.status is StepStatus.PENDING
    assert step.next_on_success is None
    assert step.next_on_failure is None
    assert step.next_on_skip is None


def test_new_plan_message_count_is_zero():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    plan = Plan(
        id="p1",
        status=PlanStatus.PENDING,
        steps=[PlanStep(id="s1", goal="Open the strait")],
        created_at=created,
        updated_at=created,
    )
    assert plan.message_count == 0


def test_plan_round_trips_through_model_dump():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    plan = Plan(
        id="p1",
        status=PlanStatus.IN_PROGRESS,
        steps=[
            PlanStep(
                id="s1",
                goal="Open the strait",
                status=StepStatus.SUCCEEDED,
                next_on_success="s2",
            )
        ],
        created_at=created,
        updated_at=created,
        message_count=2,
    )
    restored = Plan.model_validate(plan.model_dump())
    assert restored == plan
