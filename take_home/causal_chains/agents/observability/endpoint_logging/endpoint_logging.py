import logging
import time
from collections.abc import Callable


class GroupOverTime:
    """Emit one access line for this path every group_over_s seconds."""

    def __init__(self, path: str, group_over_s: float) -> None:
        self.path = path
        self.group_over_s = group_over_s


class SkipPollingEndpointPaths(logging.Filter):
    """Keep other paths. A grouped path logs once each group_over_s window."""

    def __init__(
        self,
        *policies: GroupOverTime,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()
        self.policies = policies
        self._now = now
        self._window_started_at: dict[str, float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        path = _request_path(record)
        if path is None:
            return True
        policy = _policy_for_path(self.policies, path)
        if policy is None:
            return True
        now = self._now()
        started = self._window_started_at.get(policy.path)
        if started is None or now - started >= policy.group_over_s:
            self._window_started_at[policy.path] = now
            return started is not None
        return False


def silence_some_endpoints_log() -> None:
    access = logging.getLogger("uvicorn.access")
    if any(isinstance(item, SkipPollingEndpointPaths) for item in access.filters):
        return
    access.addFilter(
        SkipPollingEndpointPaths(
            GroupOverTime(path="/health", group_over_s=600),
            GroupOverTime(path="/api/v1/causal_chains", group_over_s=300),
        )
    )


def _request_path(record: logging.LogRecord) -> str | None:
    args = record.args
    if isinstance(args, tuple) and len(args) >= 3:
        return str(args[2])
    return None


def _policy_for_path(
    policies: tuple[GroupOverTime, ...],
    path: str,
) -> GroupOverTime | None:
    for policy in policies:
        if (
            path == policy.path
            or path.startswith(policy.path + "?")
            or path.startswith(policy.path + "/")
        ):
            return policy
    return None
