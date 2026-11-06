
from backend.app.graph_schema import (
    Entity,
    Relation,
    ExtractedGraph,
    EntityType,
    RelationType
)

from backend.app.graph_store import (
    verify_connection,
    save_graph,
    close_connection
)


graph = ExtractedGraph(
    entities=[
        Entity(
            name="Alice",
            entity_type=EntityType.PERSON,
            description="A data scientist",
            source_chunk_id="chunk_001"
        ),
        Entity(
            name="Google",
            entity_type=EntityType.ORGANIZATION,
            description="A technology company",
            source_chunk_id="chunk_001"
        )
    ],

    relations=[
        Relation(
            source="Alice",
            target="Google",
            relation_type=RelationType.WORKS_AT,
            evidence_chunk_id="chunk_001"
        )
    ]
)


try:
    verify_connection()
    save_graph(graph)
    print("Entities and relationships saved successfully!")

finally:
    close_connection()
