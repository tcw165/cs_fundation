from dependency_injector import containers, providers
from neo4j import GraphDatabase

from take_home.causal_chains.agents.clients.graph_db.neo4j_client import Neo4jClient
from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache


def build_graph_db(neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> GraphDb:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    return Neo4jClient(driver)


class ClientsContainer(containers.DeclarativeContainer):
    config = providers.Configuration(
        default={
            "neo4j_uri": "bolt://graph:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "causal_chains",
        }
    )
    graph_db = providers.Singleton(
        build_graph_db,
        neo4j_uri=config.neo4j_uri,
        neo4j_user=config.neo4j_user,
        neo4j_password=config.neo4j_password,
    )
    memcache = providers.Singleton(InMemoryMemcache)
