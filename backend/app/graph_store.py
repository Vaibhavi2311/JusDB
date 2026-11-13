
import os

from neo4j import GraphDatabase
from dotenv import load_dotenv

from backend.app.entity_resolution import (
    resolve_entity_name,
    create_entity_key
)


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687"
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j"
)

NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD is missing from your .env file"
    )


# ==========================================
# CREATE NEO4J DRIVER
# ==========================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


# ==========================================
# VERIFY NEO4J CONNECTION
# ==========================================

def verify_connection():
    driver.verify_connectivity()
    print("Connected to Neo4j successfully!")


# ==========================================
# CLOSE NEO4J CONNECTION
# ==========================================

def close_connection():
    driver.close()
    print("Neo4j connection closed.")


# ==========================================
# NORMALIZE ENTITY NAME
# ==========================================

def normalize_name(name: str) -> str:
    return " ".join(
        name.strip().lower().split()
    )


# ==========================================
# SAVE GRAPH TO NEO4J
# ==========================================

def save_graph(extracted_graph):

    with driver.session() as session:

        # --------------------------------------
        # STEP 1: SAVE CANONICAL ENTITIES
        # --------------------------------------

        entity_keys = {}

        for entity in extracted_graph.entities:

            canonical_name = resolve_entity_name(
                entity.name,
                entity.entity_type.value
            )

            entity_type = entity.entity_type.value

            entity_key = create_entity_key(
                canonical_name,
                entity_type
            )

            # Map original entity name to canonical key
            lookup_name = normalize_name(entity.name)

            entity_keys[lookup_name] = entity_key

            session.run(
                """
                MERGE (e:Entity {key: $key})

                SET e.name = $name,
                    e.type = $type,
                    e.description = $description

                WITH e

                SET e.source_chunk_ids =
                    CASE
                        WHEN $chunk_id IN
                            coalesce(e.source_chunk_ids, [])
                        THEN coalesce(e.source_chunk_ids, [])
                        ELSE coalesce(e.source_chunk_ids, [])
                            + $chunk_id
                    END
                """,
                key=entity_key,
                name=canonical_name,
                type=entity_type,
                description=entity.description,
                chunk_id=entity.source_chunk_id
            )

        print("Canonical entities saved successfully!")

        # --------------------------------------
        # STEP 2: SAVE RELATIONSHIPS
        # --------------------------------------

        for relation in extracted_graph.relations:

            source_name = normalize_name(relation.source)
            target_name = normalize_name(relation.target)

            source_key = entity_keys.get(source_name)
            target_key = entity_keys.get(target_name)

            if not source_key or not target_key:
                print(
                    f"Skipping relationship: "
                    f"{relation.source} -> {relation.target}"
                )
                continue

            session.run(
                """
                MATCH (a:Entity {key: $source_key})
                MATCH (b:Entity {key: $target_key})

                MERGE (a)-[r:RELATED_TO {
                    type: $relation_type,
                    evidence_chunk_id: $evidence_chunk_id
                }]->(b)

                SET r.evidence_sentence = $evidence_sentence
                """,
                source_key=source_key,
                target_key=target_key,
                relation_type=relation.relation_type.value,
                evidence_chunk_id=relation.evidence_chunk_id,
                evidence_sentence=relation.evidence_sentence
            )

        print("Relationships saved successfully!")

    print("Graph saved successfully!")
