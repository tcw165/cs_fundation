import logging

from take_home.causal_chains.agents.observability.endpoint_logging.endpoint_logging import (
    GroupOverTime,
    SkipPollingEndpointPaths,
    silence_some_endpoints_log,
)


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _record(path: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1", "GET", path, "1.1", 200),
        exc_info=None,
    )


def test_logs_a_grouped_path_once_each_window():
    clock = _Clock()
    skip = SkipPollingEndpointPaths(
        GroupOverTime(path="/api/v1/causal_chains", group_over_s=300),
        now=clock,
    )
    assert skip.filter(_record("/api/v1/causal_chains")) is False
    clock.now = 299
    assert skip.filter(_record("/api/v1/causal_chains?limit=1")) is False
    clock.now = 300
    assert skip.filter(_record("/api/v1/causal_chains")) is True
    assert skip.filter(_record("/api/v1/causal_chains")) is False
    clock.now = 600
    assert skip.filter(_record("/api/v1/causal_chains")) is True


def test_keeps_a_path_that_has_no_policy():
    skip = SkipPollingEndpointPaths(
        GroupOverTime(path="/health", group_over_s=600),
        now=_Clock(),
    )
    assert skip.filter(_record("/api/v1/conversation/1/messages")) is True
    assert skip.filter(_record("/healthz")) is True


def test_windows_are_independent_per_path():
    clock = _Clock()
    skip = SkipPollingEndpointPaths(
        GroupOverTime(path="/health", group_over_s=600),
        GroupOverTime(path="/api/v1/causal_chains", group_over_s=300),
        now=clock,
    )
    assert skip.filter(_record("/health")) is False
    assert skip.filter(_record("/api/v1/causal_chains")) is False
    clock.now = 300
    assert skip.filter(_record("/api/v1/causal_chains")) is True
    assert skip.filter(_record("/health")) is False
    clock.now = 600
    assert skip.filter(_record("/health")) is True


def test_silence_installs_the_polling_policies_once():
    silence_some_endpoints_log()
    silence_some_endpoints_log()
    access = logging.getLogger("uvicorn.access")
    installed = [
        item
        for item in access.filters
        if isinstance(item, SkipPollingEndpointPaths)
    ]
    assert len(installed) == 1
    assert [(policy.path, policy.group_over_s) for policy in installed[0].policies] == [
        ("/health", 600),
        ("/api/v1/causal_chains", 300),
    ]
