from collections.abc import Mapping
from decimal import Decimal
from typing import override
from uuid import UUID

from neo4j import Driver

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.constants.graph import LEADS_TO_HOP_LIMIT

_P_SCALE = Decimal("0.0001")

P_QUERY = """
MATCH (root:Situation {kind: 'start'})
MATCH path = (root)-[:LEADS_TO*1..8]->(dest)
WHERE dest.situation_id IN $destination_ids
RETURN sum(reduce(acc = 1.0, r IN relationships(path) | acc * r.p)) AS p_query
"""

START_COUNT = """
MATCH (s:Situation {kind: 'start'})
RETURN count(s) AS start_count
"""

BROKEN_OUTGOING_SUMS = """
MATCH (s:Situation)-[r:LEADS_TO]->()
WITH s, sum(r.p) AS total
WHERE abs(total - 1.0) > 0.00005
RETURN s.situation_id AS situation_id, total
"""

MERGE_CASE = """
MERGE (c:Case {case_id: $case_id})
"""

GET_CASE = """
MATCH (c:Case {case_id: $case_id})
RETURN c.case_id AS case_id
"""

MERGE_SITUATION = """
MERGE (c:Case {case_id: $case_id})
MERGE (s:Situation {situation_id: $situation_id, version: $version})
SET s.desc = $desc,
    s.kind = $kind,
    s.potential_factors = $potential_factors,
    s.original_ask = $original_ask
REMOVE s.is_root
MERGE (s)-[:BELONGS_TO]->(c)
"""

REACHES_TERMINAL = f"""
MATCH (start:Situation {{situation_id: $start_situation_id, version: $start_version, kind: 'start'}})
MATCH (start)-[:BELONGS_TO]->(:Case {{case_id: $case_id}})
MATCH (terminal:Situation {{situation_id: $terminal_situation_id, version: $terminal_version, kind: 'terminal'}})
MATCH (terminal)-[:BELONGS_TO]->(:Case {{case_id: $case_id}})
RETURN EXISTS {{ MATCH (start)-[:LEADS_TO*1..{LEADS_TO_HOP_LIMIT}]->(terminal) }} AS reaches
"""

CHAIN_SO_FAR = f"""
MATCH (start:Situation {{situation_id: $start_situation_id, version: $start_version, kind: 'start'}})
MATCH (start)-[:BELONGS_TO]->(:Case {{case_id: $case_id}})
OPTIONAL MATCH path = (start)-[:LEADS_TO*0..{LEADS_TO_HOP_LIMIT}]->(current)
WHERE current.kind <> 'terminal'
  AND NOT EXISTS {{
    MATCH (current)-[:LEADS_TO]->(next)
    WHERE next.kind <> 'terminal'
  }}
  AND ALL(n IN nodes(path) WHERE n.kind <> 'terminal')
  AND EXISTS {{ MATCH (current)-[:BELONGS_TO]->(:Case {{case_id: $case_id}}) }}
RETURN start.situation_id AS start_situation_id,
    start.version AS start_version,
    start.desc AS start_desc,
    start.potential_factors AS potential_factors,
    CASE
        WHEN path IS NULL THEN []
        ELSE [n IN nodes(path)[1..] | {{
            situation_id: n.situation_id,
            version: n.version,
            desc: n.desc
        }}]
    END AS hops,
    CASE
        WHEN path IS NULL THEN []
        ELSE [i IN range(0, size(relationships(path)) - 1) | {{
            from_situation_id: nodes(path)[i].situation_id,
            from_version: nodes(path)[i].version,
            to_situation_id: nodes(path)[i + 1].situation_id,
            to_version: nodes(path)[i + 1].version,
            props: properties(relationships(path)[i])
        }}]
    END AS links
"""

LIST_LEAF_SITUATIONS = """
MATCH (start:Situation {situation_id: $start_situation_id, version: $start_version, kind: 'start'})
MATCH (start)-[:BELONGS_TO]->(:Case {case_id: $case_id})
MATCH (start)-[:LEADS_TO*1..8]->(leaf:Situation)
WHERE leaf.kind = 'situation'
  AND NOT (leaf)-[:LEADS_TO]->()
  AND EXISTS { MATCH (leaf)-[:BELONGS_TO]->(:Case {case_id: $case_id}) }
RETURN leaf.situation_id AS situation_id,
    leaf.version AS version,
    leaf.desc AS desc
"""

MERGE_LEADS_TO = """
MERGE (a:Situation {situation_id: $from_situation_id, version: $from_version})
MERGE (b:Situation {situation_id: $to_situation_id, version: $to_version})
MERGE (a)-[r:LEADS_TO]->(b)
SET r.p = $p,
    r.inputs = $inputs,
    r.from_situation_id = $from_situation_id,
    r.from_version = $from_version,
    r.to_situation_id = $to_situation_id,
    r.to_version = $to_version
"""

LIST_SITUATIONS = """
MATCH (s:Situation)-[:BELONGS_TO]->(c:Case)
RETURN s.situation_id AS situation_id,
    s.version AS version,
    s.desc AS desc,
    s.kind AS kind,
    s.potential_factors AS potential_factors,
    s.original_ask AS original_ask,
    c.case_id AS case_id
"""

CLEAR = """
MATCH (s:Situation)
DETACH DELETE s
"""

# One relationship registers the type. Deleting it leaves the type in the store.
ENSURE_LEADS_TO = """
CREATE (a:_SchemaProbe)-[:LEADS_TO]->(b:_SchemaProbe)
DETACH DELETE a, b
"""

LIST_LEADS_TO = """
MATCH (a)-[r:LEADS_TO]->(b)
RETURN a.situation_id AS from_situation_id,
    a.version AS from_version,
    b.situation_id AS to_situation_id,
    b.version AS to_version,
    properties(r) AS props
"""


def _decimal(value: object) -> Decimal:
    return Decimal(str(value)).quantize(_P_SCALE)


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _hop_rows(
    value: object,
) -> list[tuple[UUID, int, str]]:
    if not isinstance(value, list):
        return []
    rows: list[tuple[UUID, int, str]] = []
    for item in value:
        if isinstance(item, dict):
            rows.append(
                (
                    UUID(str(item["situation_id"])),
                    int(item["version"]),
                    str(item["desc"]),
                )
            )
    return rows


def _link_rows(
    value: object,
) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]:
    if not isinstance(value, list):
        return []
    rows: list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]] = []
    for item in value:
        if isinstance(item, Mapping):
            props = item["props"]
            rows.append(
                (
                    UUID(str(item["from_situation_id"])),
                    int(item["from_version"]),
                    UUID(str(item["to_situation_id"])),
                    int(item["to_version"]),
                    _decimal(props["p"]),
                    _input_rows(props["inputs"]),
                )
            )
    return rows


def _input_rows(
    value: object,
) -> list[tuple[str, Decimal]]:
    if not isinstance(value, list):
        return []
    rows: list[tuple[str, Decimal]] = []
    for item in value:
        if isinstance(item, dict):
            rows.append((str(item["name"]), _decimal(item["value"])))
    return rows


class Neo4jClient(GraphDb):
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def ensure_leads_to(self) -> None:
        with self._driver.session() as session:
            session.run(ENSURE_LEADS_TO).consume()

    @override
    def p_query(self, destination_ids: list[UUID]) -> Decimal:
        with self._driver.session() as session:
            record = session.run(
                P_QUERY,
                destination_ids=[str(situation_id) for situation_id in destination_ids],
            ).single()
        if record is None or record["p_query"] is None:
            return Decimal("0.0000")
        return _decimal(record["p_query"])

    @override
    def start_count(self) -> int:
        with self._driver.session() as session:
            record = session.run(START_COUNT).single()
        if record is None:
            return 0
        return int(record["start_count"])

    @override
    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]:
        with self._driver.session() as session:
            records = list(session.run(BROKEN_OUTGOING_SUMS))
        rows: list[tuple[UUID, Decimal]] = []
        for record in records:
            rows.append((UUID(str(record["situation_id"])), _decimal(record["total"])))
        return rows

    @override
    def merge_case(self, case_id: UUID) -> None:
        with self._driver.session() as session:
            session.run(MERGE_CASE, case_id=str(case_id))

    @override
    def get_case(self, case_id: UUID) -> UUID | None:
        with self._driver.session() as session:
            record = session.run(GET_CASE, case_id=str(case_id)).single()
        if record is None or record["case_id"] is None:
            return None
        return UUID(str(record["case_id"]))

    @override
    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        desc: str,
        case_id: UUID,
        kind: str,
        potential_factors: list[str],
        original_ask: str,
    ) -> None:
        with self._driver.session() as session:
            session.run(
                MERGE_SITUATION,
                situation_id=str(situation_id),
                version=version,
                desc=desc,
                case_id=str(case_id),
                kind=kind,
                potential_factors=potential_factors,
                original_ask=original_ask,
            )

    @override
    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, Decimal]],
    ) -> None:
        with self._driver.session() as session:
            session.run(
                MERGE_LEADS_TO,
                from_situation_id=str(from_situation_id),
                from_version=from_version,
                to_situation_id=str(to_situation_id),
                to_version=to_version,
                p=float(p),
                inputs=[
                    {"name": name, "value": float(value)}
                    for name, value in inputs
                ],
            )

    @override
    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, str, list[str], str, UUID]]:
        with self._driver.session() as session:
            records = list(session.run(LIST_SITUATIONS))
        rows: list[tuple[UUID, int, str, str, list[str], str, UUID]] = []
        for record in records:
            original_ask = record["original_ask"]
            rows.append(
                (
                    UUID(str(record["situation_id"])),
                    int(record["version"]),
                    str(record["desc"]),
                    str(record["kind"]),
                    _strings(record["potential_factors"]),
                    "" if original_ask is None else str(original_ask),
                    UUID(str(record["case_id"])),
                )
            )
        return rows

    @override
    def list_leaf_situations(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> list[tuple[UUID, int, str]]:
        with self._driver.session() as session:
            records = list(
                session.run(
                    LIST_LEAF_SITUATIONS,
                    case_id=str(case_id),
                    start_situation_id=str(start_situation_id),
                    start_version=start_version,
                )
            )
        rows: list[tuple[UUID, int, str]] = []
        for record in records:
            rows.append(
                (
                    UUID(str(record["situation_id"])),
                    int(record["version"]),
                    str(record["desc"]),
                )
            )
        return rows

    @override
    def reaches_terminal(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
        terminal_situation_id: UUID,
        terminal_version: int,
    ) -> bool:
        with self._driver.session() as session:
            record = session.run(
                REACHES_TERMINAL,
                case_id=str(case_id),
                start_situation_id=str(start_situation_id),
                start_version=start_version,
                terminal_situation_id=str(terminal_situation_id),
                terminal_version=terminal_version,
            ).single()
        if record is None or record["reaches"] is None:
            return False
        return bool(record["reaches"])

    @override
    def lookup_chain_so_far(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> tuple[
        tuple[UUID, int, str, list[str]],
        list[tuple[UUID, int, str]],
        list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]],
    ] | None:
        with self._driver.session() as session:
            record = session.run(
                CHAIN_SO_FAR,
                case_id=str(case_id),
                start_situation_id=str(start_situation_id),
                start_version=start_version,
            ).single()
        if record is None:
            return None
        return (
            (
                UUID(str(record["start_situation_id"])),
                int(record["start_version"]),
                str(record["start_desc"]),
                _strings(record["potential_factors"]),
            ),
            _hop_rows(record["hops"]),
            _link_rows(record["links"]),
        )

    @override
    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]:
        with self._driver.session() as session:
            records = list(session.run(LIST_LEADS_TO))
        return _link_rows(records)

    @override
    def clear(self) -> None:
        with self._driver.session() as session:
            session.run(CLEAR)
