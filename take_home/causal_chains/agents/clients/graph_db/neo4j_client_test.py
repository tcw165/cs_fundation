from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.clients.graph_db.neo4j_client import Neo4jClient
from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb

CLEAR_ID = UUID("44444444-4444-4444-8444-444444444444")
RESUMES_ID = UUID("66666666-6666-4666-8666-666666666666")
NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


class _Result:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records

    def single(self) -> dict[str, object] | None:
        if not self._records:
            return None
        return self._records[0]

    def __iter__(self):
        return iter(self._records)


class _Session:
    def __init__(
        self,
        records: list[dict[str, object]],
        calls: list[tuple[str, dict[str, object]]],
    ) -> None:
        self._records = records
        self._calls = calls

    def __enter__(self) -> "_Session":
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def run(
        self,
        query: str,
        **params: object,
    ) -> _Result:
        self._calls.append((query, params))
        return _Result(self._records)


class _Driver:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self._records = records
        self.calls: list[tuple[str, dict[str, object]]] = []

    def session(self) -> _Session:
        return _Session(self._records, self.calls)


def test_neo4j_client_subclasses_graph_db():
    assert issubclass(Neo4jClient, GraphDb)


def test_p_query_reads_fake_sum():
    client = Neo4jClient(_Driver([{"p_query": Decimal("0.0206")}]))
    assert client.p_query([CLEAR_ID, RESUMES_ID]) == Decimal("0.0206")


def test_root_count_reads_fake_count():
    client = Neo4jClient(_Driver([{"root_count": 1}]))
    assert client.root_count() == 1


def test_broken_outgoing_sums_reads_fake_rows():
    client = Neo4jClient(_Driver([{"situation_id": str(NOW_ID), "total": Decimal("0.9000")}]))
    assert client.broken_outgoing_sums() == [(NOW_ID, Decimal("0.9000"))]


def test_merge_situation_writes_node_fields():
    driver = _Driver([])
    client = Neo4jClient(driver)
    client.merge_situation(NOW_ID, "now", True)
    query, params = driver.calls[0]
    assert "MERGE (s:Situation {situation_id: $situation_id})" in query
    assert params == {
        "situation_id": str(NOW_ID),
        "desc": "now",
        "is_root": True,
    }


def test_merge_leads_to_writes_float_p():
    driver = _Driver([])
    client = Neo4jClient(driver)
    client.merge_leads_to(NOW_ID, CLEAR_ID, Decimal("0.5"))
    query, params = driver.calls[0]
    assert "MERGE (a)-[r:LEADS_TO]->(b)" in query
    assert params == {
        "from_situation_id": str(NOW_ID),
        "to_situation_id": str(CLEAR_ID),
        "p": 0.5,
    }
    assert isinstance(params["p"], float)
