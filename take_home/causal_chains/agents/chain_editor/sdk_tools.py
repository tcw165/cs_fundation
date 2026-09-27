import json
from decimal import Decimal, InvalidOperation
from uuid import UUID

from agents import function_tool

from take_home.causal_chains.agents.chain_editor.protocol.protocol import ChainEditor
from take_home.causal_chains.agents.models.causal_chain.evidence import Evidence
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs


def sdk_tools(editor: ChainEditor, names: tuple[str, ...]) -> list[object]:
    """Build SDK tools closed over one editor.

    names selects the tools, in that order. A tool error is returned as text
    so the agent can respect a depth or child-cap refusal.
    """

    def _call(action):
        try:
            return action()
        except (ValueError, InvalidOperation) as error:
            return str(error)

    @function_tool
    def get_chain() -> str:
        """Read the chain, including inputs, raw_p, p, and stale flags."""
        return editor.get_chain().model_dump_json()

    @function_tool
    def get_event(event_id: str) -> str:
        """Read one event by id."""
        return _call(lambda: editor.get_event(UUID(event_id)).model_dump_json())

    @function_tool
    def list_effects(event_id: str) -> str:
        """List the outgoing links of one event."""

        def action() -> str:
            links = editor.list_effects(UUID(event_id))
            return json.dumps([link.model_dump(mode="json") for link in links])

        return _call(action)

    @function_tool
    def p_query() -> str:
        """Sum path products into destinations inside the depth bounds."""
        return str(editor.p_query())

    @function_tool
    def add_event(statement: str, cause_id: str) -> str:
        """Add an event. Pass an empty cause_id to add the root.

        Depth is assigned here. A hop past max depth is rejected.
        """
        parent = UUID(cause_id) if cause_id else None
        return _call(lambda: editor.add_event(statement, parent).model_dump_json())

    @function_tool
    def set_event(event_id: str, statement: str) -> str:
        """Change an event statement. Descendant links become stale and lose p."""
        return _call(lambda: editor.set_event(UUID(event_id), statement).model_dump_json())

    @function_tool
    def add_link(cause_id: str, effect_id: str) -> str:
        """Link a cause to an effect created under it. Does not set p."""
        return _call(lambda: editor.add_link(UUID(cause_id), UUID(effect_id)).model_dump_json())

    @function_tool
    def set_link_inputs(
        link_id: str,
        base_rate: str,
        notes: list[str],
        log_odds: list[str],
    ) -> str:
        """Set the inputs that decide this link's probability. Do not pass p.

        notes and log_odds are paired. base_rate is a decimal string in (0, 1).
        Each log_odds value is a decimal string from -2 to 2.
        """

        def action() -> str:
            if len(notes) != len(log_odds):
                raise ValueError("notes and log_odds differ in length")
            inputs = LinkInputs(
                base_rate=Decimal(base_rate),
                evidence=[
                    Evidence(note=note, log_odds=Decimal(odd))
                    for note, odd in zip(notes, log_odds, strict=True)
                ],
            )
            return editor.set_link_inputs(UUID(link_id), inputs).model_dump_json()

        return _call(action)

    @function_tool
    def mark_destination(event_id: str) -> str:
        """Mark an event as a dated outcome of the query."""
        return _call(lambda: editor.mark_destination(UUID(event_id)).model_dump_json())

    tools = {
        "get_chain": get_chain,
        "get_event": get_event,
        "list_effects": list_effects,
        "p_query": p_query,
        "add_event": add_event,
        "set_event": set_event,
        "add_link": add_link,
        "set_link_inputs": set_link_inputs,
        "mark_destination": mark_destination,
    }
    missing = [name for name in names if name not in tools]
    if missing:
        raise ValueError(f"unknown tool {missing[0]}")
    return [tools[name] for name in names]
