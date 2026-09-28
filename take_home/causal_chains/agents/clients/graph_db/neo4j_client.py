from decimal import Decimal
from typing import override
from uuid import UUID

from neo4j import Driver

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb

_P_SCALE = Decimal("0.0001")

P_QUERY = """
MATCH (root:Situation {is_root: true})
MATCH path = (root)-[:LEADS_TO*1..8]->(dest)
WHERE dest.situation_id IN $destination_ids
RETURN sum(reduce(acc = 1.0, r IN relationships(path) | acc * r.p)) AS p_query
"""

ROOT_COUNT = """
MATCH (s:Situation {is_root: true})
RETURN count(s) AS root_count
"""

BROKEN_OUTGOING_SUMS = """
MATCH (s:Situation)-[r:LEADS_TO]->()
WITH s, sum(r.p) AS total
WHERE abs(total - 1.0) > 0.00005
RETURN s.situation_id AS situation_id, total
"""

MERGE_SITUATION = """
MERGE (s:Situation {situation_id: $situation_id, version: $version})
SET s.desc = $desc, s.is_root = $is_root
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
MATCH (s:Situation)
RETURN s.situation_id AS situation_id,
    s.version AS version,
    s.desc AS desc,
    s.is_root AS is_root
"""

CLEAR = """
MATCH (s:Situation)
DETACH DELETE s
"""

LIST_LEADS_TO = """
MATCH ()-[r:LEADS_TO]->()
RETURN r.from_situation_id AS from_situation_id,
    r.from_version AS from_version,
    r.to_situation_id AS to_situation_id,
    r.to_version AS to_version,
    r.p AS p,
    r.inputs AS inputs
"""


def _decimal(value: object) -> Decimal:
    return Decimal(str(value)).quantize(_P_SCALE)


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
    def root_count(self) -> int:
        with self._driver.session() as session:
            record = session.run(ROOT_COUNT).single()
        if record is None:
            return 0
        return int(record["root_count"])

    @override
    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]:
        with self._driver.session() as session:
            records = list(session.run(BROKEN_OUTGOING_SUMS))
        rows: list[tuple[UUID, Decimal]] = []
        for record in records:
            rows.append((UUID(str(record["situation_id"])), _decimal(record["total"])))
        return rows

    @override
    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        desc: str,
        is_root: bool,
    ) -> None:
        with self._driver.session() as session:
            session.run(
                MERGE_SITUATION,
                situation_id=str(situation_id),
                version=version,
                desc=desc,
                is_root=is_root,
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
    ) -> list[tuple[UUID, int, str, bool]]:
        with self._driver.session() as session:
            records = list(session.run(LIST_SITUATIONS))
        rows: list[tuple[UUID, int, str, bool]] = []
        for record in records:
            rows.append(
                (
                    UUID(str(record["situation_id"])),
                    int(record["version"]),
                    str(record["desc"]),
                    bool(record["is_root"]),
                )
            )
        return rows

    @override
    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]:
        with self._driver.session() as session:
            records = list(session.run(LIST_LEADS_TO))
        rows: list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]] = []
        for record in records:
            rows.append(
                (
                    UUID(str(record["from_situation_id"])),
                    int(record["from_version"]),
                    UUID(str(record["to_situation_id"])),
                    int(record["to_version"]),
                    _decimal(record["p"]),
                    _input_rows(record["inputs"]),
                )
            )
        return rows

    @override
    def clear(self) -> None:
        with self._driver.session() as session:
            session.run(CLEAR)
