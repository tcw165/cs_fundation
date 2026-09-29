from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.clients.graph_db.neo4j_client import (
    CLEAR,
    Neo4jClient,
)
from take_home.causal_chains.agents.constants.graph import LEADS_TO_HOP_LIMIT
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


def test_start_count_reads_fake_count():
    client = Neo4jClient(_Driver([{"start_count": 1}]))
    assert client.start_count() == 1


def test_broken_outgoing_sums_reads_fake_rows():
    client = Neo4jClient(_Driver([{"situation_id": str(NOW_ID), "total": Decimal("0.9000")}]))
    assert client.broken_outgoing_sums() == [(NOW_ID, Decimal("0.9000"))]


def test_merge_case_and_get_case_use_the_case_id():
    driver = _Driver([{"case_id": str(NOW_ID)}])
    client = Neo4jClient(driver)
    client.merge_case(NOW_ID)
    assert client.get_case(NOW_ID) == NOW_ID
    merge_query, merge_params = driver.calls[0]
    get_query, get_params = driver.calls[1]
    assert "MERGE (c:Case {case_id: $case_id})" in merge_query
    assert merge_params == {"case_id": str(NOW_ID)}
    assert "MATCH (c:Case {case_id: $case_id})" in get_query
    assert get_params == {"case_id": str(NOW_ID)}


def test_get_case_returns_none_when_missing():
    client = Neo4jClient(_Driver([]))
    assert client.get_case(NOW_ID) is None


def test_merge_situation_writes_node_fields():
    driver = _Driver([])
    client = Neo4jClient(driver)
    client.merge_situation(NOW_ID, 1, "now", CLEAR_ID, "start", ["blockade"], "")
    query, params = driver.calls[0]
    assert "MERGE (s:Situation {situation_id: $situation_id, version: $version})" in query
    assert "MERGE (s)-[:BELONGS_TO]->(c)" in query
    assert params == {
        "situation_id": str(NOW_ID),
        "version": 1,
        "desc": "now",
        "case_id": str(CLEAR_ID),
        "kind": "start",
        "potential_factors": ["blockade"],
        "original_ask": "",
    }


def test_merge_leads_to_writes_float_p():
    driver = _Driver([])
    client = Neo4jClient(driver)
    client.merge_leads_to(
        NOW_ID,
        1,
        CLEAR_ID,
        1,
        Decimal("0.5"),
        [("deal_odds", Decimal("0.5"))],
    )
    query, params = driver.calls[0]
    assert "MERGE (a)-[r:LEADS_TO]->(b)" in query
    assert "r.from_version = $from_version" in query
    assert "r.to_version = $to_version" in query
    assert params == {
        "from_situation_id": str(NOW_ID),
        "from_version": 1,
        "to_situation_id": str(CLEAR_ID),
        "to_version": 1,
        "p": 0.5,
        "inputs": [{"name": "deal_odds", "value": 0.5}],
    }
    assert isinstance(params["p"], float)
    assert isinstance(params["inputs"][0]["value"], float)


def test_list_situations_reads_versioned_rows():
    client = Neo4jClient(
        _Driver(
            [
                {
                    "situation_id": str(NOW_ID),
                    "version": 1,
                    "desc": "now",
                    "kind": "start",
                    "potential_factors": ["blockade"],
                    "original_ask": "",
                    "case_id": str(CLEAR_ID),
                }
            ]
        )
    )
    assert client.list_situations() == [
        (NOW_ID, 1, "now", "start", ["blockade"], "", CLEAR_ID),
    ]
    assert "MATCH (s:Situation)-[:BELONGS_TO]->(c:Case)" in client._driver.calls[0][0]


def test_list_leaf_situations_walks_from_the_start():
    client = Neo4jClient(
        _Driver(
            [
                {
                    "situation_id": str(RESUMES_ID),
                    "version": 1,
                    "desc": "leaf",
                }
            ]
        )
    )
    assert client.list_leaf_situations(CLEAR_ID, NOW_ID, 1) == [(RESUMES_ID, 1, "leaf")]
    query, params = client._driver.calls[0]
    assert "kind = 'situation'" in query
    assert "NOT (leaf)-[:LEADS_TO]->()" in query
    assert params == {
        "case_id": str(CLEAR_ID),
        "start_situation_id": str(NOW_ID),
        "start_version": 1,
    }


def test_reaches_terminal_walks_to_the_terminal():
    client = Neo4jClient(_Driver([{"reaches": True}]))
    assert client.reaches_terminal(CLEAR_ID, NOW_ID, 1, RESUMES_ID, 1) is True
    query, params = client._driver.calls[0]
    assert "kind: 'start'" in query
    assert "kind: 'terminal'" in query
    assert f"[:LEADS_TO*1..{LEADS_TO_HOP_LIMIT}]" in query
    assert params == {
        "case_id": str(CLEAR_ID),
        "start_situation_id": str(NOW_ID),
        "start_version": 1,
        "terminal_situation_id": str(RESUMES_ID),
        "terminal_version": 1,
    }


def test_lookup_chain_so_far_reads_the_open_line():
    client = Neo4jClient(
        _Driver(
            [
                {
                    "start_situation_id": str(NOW_ID),
                    "start_version": 1,
                    "start_desc": "now",
                    "potential_factors": ["blockade"],
                    "hops": [],
                    "links": [],
                }
            ]
        )
    )
    assert client.lookup_chain_so_far(CLEAR_ID, NOW_ID, 1) == (
        (NOW_ID, 1, "now", ["blockade"]),
        [],
        [],
    )
    query, params = client._driver.calls[0]
    assert f"[:LEADS_TO*0..{LEADS_TO_HOP_LIMIT}]" in query
    assert "kind <> 'terminal'" in query
    assert "r.from_situation_id" not in query
    assert "r.inputs" not in query
    assert "properties(relationships(path)[i])" in query
    assert params == {
        "case_id": str(CLEAR_ID),
        "start_situation_id": str(NOW_ID),
        "start_version": 1,
    }


def test_lookup_chain_so_far_reads_one_hop():
    client = Neo4jClient(
        _Driver(
            [
                {
                    "start_situation_id": str(NOW_ID),
                    "start_version": 1,
                    "start_desc": "now",
                    "potential_factors": ["blockade"],
                    "hops": [
                        {
                            "situation_id": str(RESUMES_ID),
                            "version": 1,
                            "desc": "talks open",
                        }
                    ],
                    "links": [
                        {
                            "from_situation_id": str(NOW_ID),
                            "from_version": 1,
                            "to_situation_id": str(RESUMES_ID),
                            "to_version": 1,
                            "props": {
                                "p": 0.5,
                                "inputs": [{"name": "deal_odds", "value": 0.5}],
                            },
                        }
                    ],
                }
            ]
        )
    )
    start_row, hops, links = client.lookup_chain_so_far(CLEAR_ID, NOW_ID, 1)
    assert start_row[0] == NOW_ID
    assert hops == [(RESUMES_ID, 1, "talks open")]
    assert links[0][0] == NOW_ID
    assert links[0][2] == RESUMES_ID
    assert links[0][4] == Decimal("0.5000")
    assert links[0][5] == [("deal_odds", Decimal("0.5000"))]


def test_lookup_chain_so_far_is_missing_when_the_row_is_missing():
    client = Neo4jClient(_Driver([]))
    assert client.lookup_chain_so_far(CLEAR_ID, NOW_ID, 1) is None


def test_reaches_terminal_is_false_when_the_row_is_missing():
    client = Neo4jClient(_Driver([]))
    assert client.reaches_terminal(CLEAR_ID, NOW_ID, 1, RESUMES_ID, 1) is False


def test_list_leads_to_reads_versioned_rows():
    client = Neo4jClient(
        _Driver(
            [
                {
                    "from_situation_id": str(NOW_ID),
                    "from_version": 1,
                    "to_situation_id": str(CLEAR_ID),
                    "to_version": 1,
                    "props": {
                        "p": 0.5,
                        "inputs": [{"name": "deal_odds", "value": 0.5}],
                    },
                }
            ]
        )
    )
    assert client.list_leads_to() == [
        (
            NOW_ID,
            1,
            CLEAR_ID,
            1,
            Decimal("0.5000"),
            [("deal_odds", Decimal("0.5000"))],
        ),
    ]
    assert "MATCH (a)-[r:LEADS_TO]->(b)" in client._driver.calls[0][0]
    assert "r.from_situation_id" not in client._driver.calls[0][0]
    assert "properties(r)" in client._driver.calls[0][0]


def test_clear_deletes_situations():
    driver = _Driver([])
    client = Neo4jClient(driver)
    client.clear()
    query, params = driver.calls[0]
    assert query == CLEAR
    assert "DETACH DELETE s" in query
    assert params == {}
