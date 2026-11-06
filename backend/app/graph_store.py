
import os

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD is missing from your .env file")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


def verify_connection():
    driver.verify_connectivity()
    print("Connected to Neo4j successfully!")


def close_connection():
    driver.close()


def normalize_name(name):
    return " ".join(name.strip().lower().split())


def save_graph(extracted_graph):
    with driver.session() as session:

        # Save entities as graph nodes
        for entity in extracted_graph.entities:
            entity_key = (
                entity.entity_type.value + ":" +
                normalize_name(entity.name)
            )

            session.run(
                """
                MERGE (e:Entity {key: $key})
                SET e.name = $name,
                    e.type = $type,
                    e.description = $description
                """,
                key=entity_key,
                name=entity.name,
                type=entity.entity_type.value,
                description=entity.description
            )

        # Map entity names to their graph keys
        entity_keys = {
            normalize_name(entity.name): (
                entity.entity_type.value + ":" +
                normalize_name(entity.name)
            )
            for entity in extracted_graph.entities
        }

        # Save relationships and their evidence
        for relation in extracted_graph.relations:
            source_key = entity_keys.get(
                normalize_name(relation.source)
            )
            target_key = entity_keys.get(
                normalize_name(relation.target)
            )

            if not source_key or not target_key:
                continue

            session.run(
                """
                MATCH (a:Entity {key: $source_key})
                MATCH (b:Entity {key: $target_key})
                MERGE (a)-[r:RELATED_TO {
                    type: $relation_type,
                    evidence_chunk_id: $evidence_chunk_id
                }]->(b)
                """,
                source_key=source_key,
                target_key=target_key,
                relation_type=relation.relation_type.value,
                evidence_chunk_id=relation.evidence_chunk_id
            )
