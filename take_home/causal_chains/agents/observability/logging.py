import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from logging import Logger, LoggerAdapter

_LOGGER_NAME = "agents"
_session_logger: ContextVar[LoggerAdapter[Logger]] = ContextVar("session_logger")


def logger() -> LoggerAdapter[Logger]:
    try:
        return _session_logger.get()
    except LookupError:
        return LoggerAdapter(logging.getLogger(_LOGGER_NAME), {})


@contextmanager
def bind_logger(
    extra: dict[str, str] = {},
) -> Iterator[LoggerAdapter[Logger]]:
    named = logging.getLogger(_LOGGER_NAME)
    adapter = LoggerAdapter(
        named,
        extra,
    )
    token = _session_logger.set(adapter)
    try:
        yield adapter
    finally:
        _session_logger.reset(token)


@contextmanager
def bind_session_logger(
    conversation_id: str,
    turn_id: str,
) -> Iterator[LoggerAdapter[Logger]]:
    named = logging.getLogger(_LOGGER_NAME)
    if not named.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                "%(levelname)s %(name)s conversation_id=%(conversation_id)s turn_id=%(turn_id)s %(message)s",
                defaults={"conversation_id": "", "turn_id": ""},
            ),
        )
        named.addHandler(handler)
        named.setLevel(logging.INFO)
        named.propagate = False
    adapter = LoggerAdapter(
        named,
        {"conversation_id": conversation_id, "turn_id": turn_id},
    )
    token = _session_logger.set(adapter)
    try:
        yield adapter
    finally:
        _session_logger.reset(token)


def bind_conversation_logger(conversation_id: str) -> Iterator[LoggerAdapter[Logger]]:
    return bind_session_logger(conversation_id, "")
