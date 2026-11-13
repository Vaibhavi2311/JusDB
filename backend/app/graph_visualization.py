
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from backend.app.entity_resolution import create_entity_key

load_dotenv()


def get_graph_visualization(
    entity_name: str,
    entity_type: str,
    limit: int = 100
):
    """
    Fetch an entity and its directly connected
    entities and relationships from Neo4j.
    """

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        raise ValueError("NEO4J_PASSWORD is not configured")

    entity_key = create_entity_key(
        entity_name,
        entity_type
    )

    nodes = {}
    edges = {}

    query = """
    MATCH (center:Entity {key: $entity_key})

    OPTIONAL MATCH (center)-[r:RELATED_TO]-(neighbor:Entity)

    RETURN
        center,
        r,
        neighbor,
        CASE
            WHEN r IS NULL THEN null
            ELSE startNode(r)
        END AS start_node,
        CASE
            WHEN r IS NULL THEN null
            ELSE endNode(r)
        END AS end_node

    LIMIT $limit
    """

    with GraphDatabase.driver(
        uri,
        auth=(username, password)
    ) as driver:

        driver.verify_connectivity()

        with driver.session() as session:

            records = session.run(
                query,
                entity_key=entity_key,
                limit=limit
            )

            for record in records:

                center = record["center"]
                neighbor = record["neighbor"]
                relationship = record["r"]

                # Add center entity
                center_key = center["key"]

                nodes[center_key] = {
                    "data": {
                        "id": center_key,
                        "label": center.get("name", ""),
                        "type": center.get("type", ""),
                        "description": center.get(
                            "description", ""
                        )
                    }
                }

                # Add connected entity and relationship
                if neighbor is not None and relationship is not None:

                    neighbor_key = neighbor["key"]

                    nodes[neighbor_key] = {
                        "data": {
                            "id": neighbor_key,
                            "label": neighbor.get("name", ""),
                            "type": neighbor.get("type", ""),
                            "description": neighbor.get(
                                "description", ""
                            )
                        }
                    }

                    start_node = record["start_node"]
                    end_node = record["end_node"]

                    edge_id = relationship.element_id

                    edges[edge_id] = {
                        "data": {
                            "id": edge_id,
                            "source": start_node["key"],
                            "target": end_node["key"],
                            "label": relationship.get(
                                "type", "RELATED_TO"
                            ),
                            "evidence_chunk_id": relationship.get(
                                "evidence_chunk_id", ""
                            ),
                            "evidence_sentence": relationship.get(
                                "evidence_sentence", ""
                            )
                        }
                    }

    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values())
    }
