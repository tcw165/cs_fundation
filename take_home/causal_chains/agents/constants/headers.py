class _Frozen(type):
    def __setattr__(cls, name: str, value: object) -> None:
        raise TypeError(f"{cls.__name__} is frozen")


class MessagingConstants(metaclass=_Frozen):
    SHORT_POLL_INTERVAL_MS = 1000
    SHORT_POLL_INTERVAL_HEADER = "x-short-poll-interval-ms"
