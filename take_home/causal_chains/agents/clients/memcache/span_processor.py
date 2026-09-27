import json
from typing import Any, override

from agents.tracing import Span, Trace, TracingProcessor

from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache


class MemcacheSpanProcessor(TracingProcessor):
    def __init__(self, memcache: Memcache) -> None:
        self._memcache = memcache

    @override
    def on_trace_start(self, trace: Trace) -> None:
        return None

    @override
    def on_trace_end(self, trace: Trace) -> None:
        return None

    @override
    def on_span_start(self, span: Span[Any]) -> None:
        return None

    @override
    def on_span_end(self, span: Span[Any]) -> None:
        exported = span.export()
        if exported is None:
            return
        self._memcache.append(json.dumps(exported) + "\n")

    @override
    def shutdown(self) -> None:
        return None

    @override
    def force_flush(self) -> None:
        return None
