from enum import StrEnum


class TurnStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    timeout = "timeout"

    def is_ended(self) -> bool:
        return self in {
            TurnStatus.completed,
            TurnStatus.failed,
            TurnStatus.cancelled,
            TurnStatus.timeout,
        }
