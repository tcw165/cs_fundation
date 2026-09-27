from decimal import Decimal
from typing import override
from uuid import UUID

from neo4j import Driver

from take_home.causal_chains.agents.clients.graph_db.protocol import GraphDb

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


def _decimal(value: object) -> Decimal:
    return Decimal(str(value)).quantize(_P_SCALE)


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
