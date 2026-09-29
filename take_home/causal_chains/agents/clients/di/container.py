import boto3
from dependency_injector import containers, providers
from neo4j import GraphDatabase

from take_home.causal_chains.agents.clients.dynamo_db.boto_dynamo_db import BotoDynamoDb
from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
from take_home.causal_chains.agents.clients.graph_db.neo4j_client import Neo4jClient
from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.clients.memcache.span_processor import MemcacheSpanProcessor


def build_graph_db(neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> GraphDb:
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    client = Neo4jClient(driver)
    client.ensure_leads_to()
    return client


def build_dynamo_db(
    endpoint_url: str,
    region_name: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
) -> DynamoDb:
    client = boto3.client(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    return BotoDynamoDb(client)


class ClientsContainer(containers.DeclarativeContainer):
    config = providers.Configuration(
        default={
            "neo4j_uri": "bolt://graph:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "causal_chains",
            "dynamodb_endpoint_url": "http://dynamodb:8000",
            "dynamodb_region": "us-east-1",
            "dynamodb_access_key_id": "dummy",
            "dynamodb_secret_access_key": "dummy",
        }
    )
    graph_db = providers.Singleton(
        build_graph_db,
        neo4j_uri=config.neo4j_uri,
        neo4j_user=config.neo4j_user,
        neo4j_password=config.neo4j_password,
    )
    dynamo_db = providers.Singleton(
        build_dynamo_db,
        endpoint_url=config.dynamodb_endpoint_url,
        region_name=config.dynamodb_region,
        aws_access_key_id=config.dynamodb_access_key_id,
        aws_secret_access_key=config.dynamodb_secret_access_key,
    )
    memcache = providers.Singleton(InMemoryMemcache)
    span_processor = providers.Singleton(MemcacheSpanProcessor, memcache=memcache)
