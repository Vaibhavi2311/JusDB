
from backend.app.graph_store import driver
from backend.app.entity_resolution import (
    resolve_entity_name,
    create_entity_key
)


def search_graph_entity(entity_name: str, entity_type: str):
    """
    Find an entity using its canonical name and type.
    """

    canonical_name = resolve_entity_name(
        entity_name,
        entity_type
    )

    entity_key = create_entity_key(
        entity_name,
        entity_type
    )

    with driver.session() as session:

        result = session.run(
            """
            MATCH (e:Entity {key: $entity_key})
            RETURN
                e.name AS name,
                e.type AS type,
                e.description AS description,
                e.source_chunk_ids AS source_chunk_ids
            """,
            entity_key=entity_key
        )

        records = [record.data() for record in result]

    return records


def get_entity_relationships(entity_name: str, entity_type: str):
    """
    Find entities directly connected to the given entity.
    """

    entity_key = create_entity_key(
        entity_name,
        entity_type
    )

    with driver.session() as session:

        result = session.run(
            """
            MATCH (start:Entity {key: $entity_key})
                  -[r:RELATED_TO]-(connected:Entity)

            RETURN
                start.name AS start_entity,
                r.type AS relationship,
                connected.name AS connected_entity,
                connected.type AS connected_type,
                r.evidence_sentence AS evidence,
                r.evidence_chunk_id AS evidence_chunk_id

            LIMIT 50
            """,
            entity_key=entity_key
        )

        records = [record.data() for record in result]

    return records


def multi_hop_search(
    entity_name: str,
    entity_type: str,
    max_hops: int = 2
):
    """
    Retrieve entities connected within a specified
    number of relationship steps.
    """

    if not isinstance(max_hops, int) or not 1 <= max_hops <= 3:
        raise ValueError("max_hops must be between 1 and 3")

    entity_key = create_entity_key(
        entity_name,
        entity_type
    )

    with driver.session() as session:

        result = session.run(
            """
            MATCH path =
                (start:Entity {key: $entity_key})
                -[*1..3]-(connected:Entity)

            WHERE length(path) <= $max_hops

            RETURN
                [node IN nodes(path) |
                    {
                        name: node.name,
                        type: node.type,
                        description: node.description
                    }
                ] AS entities,

                [rel IN relationships(path) |
                    {
                        type: rel.type,
                        evidence: rel.evidence_sentence,
                        evidence_chunk_id: rel.evidence_chunk_id
                    }
                ] AS relationships

            LIMIT 50
            """,
            entity_key=entity_key,
            max_hops=max_hops
        )

        records = [record.data() for record in result]

    return records
