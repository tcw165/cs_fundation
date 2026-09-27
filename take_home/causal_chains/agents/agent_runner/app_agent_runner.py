from collections.abc import AsyncGenerator
from typing import override

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agents.crystal_ball.chain_graph import ChainGraph
from take_home.causal_chains.agents.clients.memcache.protocol.protocol import Memcache
from take_home.causal_chains.agents.agents.crystal_ball.crystal_ball import crystal_ball
from take_home.causal_chains.agents.agents.crystal_ball.examine import examine
from take_home.causal_chains.agents.models.messaging.sse_event import (
    RunTraces,
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseTool,
)
from take_home.causal_chains.agents.models.run_context import RunContext


class AppAgentRunner(AgentRunner):
    def __init__(self, api_key: str, memcache: Memcache) -> None:
        self._api_key = api_key
        self._memcache = memcache

    @override
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AsyncGenerator[SseEvent]:
        kept_graph = None
        kept_score = -1
        critique = ""
        results: list[object] = []
        try:
            for _ in range(3):
                prompt = "\n".join(inputs)
                if critique:
                    prompt = f"{prompt}\n{critique}"
                result = Runner.run_streamed(
                    crystal_ball,
                    input=prompt,
                    context=context,
                )
                results.append(result)
                async for event in result.stream_events():
                    if event.type == "raw_response_event":
                        data = getattr(event, "data", None)
                        if isinstance(data, ResponseTextDeltaEvent):
                            yield SseDelta(text=data.delta)
                        continue
                    if event.type == "run_item_stream_event":
                        item = getattr(event, "item", None)
                        item_type = getattr(item, "type", "")
                        if item_type == "tool_call_item":
                            name = getattr(getattr(item, "raw_item", None), "name", "tool")
                            yield SseTool(name=str(name), status="called")
                graph = getattr(result, "final_output", None)
                if not isinstance(graph, ChainGraph):
                    break
                exam = examine(graph)
                yield SseDelta(text=f"score {exam.score}\n")
                if exam.score <= kept_score:
                    break
                kept_graph = graph
                kept_score = exam.score
                critique = exam.failures[0] if exam.failures else ""
                if not critique:
                    break
            if kept_graph is not None:
                yield SseDelta(text=kept_graph.model_dump_json())
            yield RunTraces(text=self._memcache.flush())
            yield SseDone(message_id=f"m_{context.turn_id}")
        except Exception as error:
            yield SseError(message=str(error))
        finally:
            for result in results:
                cancel = getattr(result, "cancel", None)
                if cancel is not None:
                    cancel()
