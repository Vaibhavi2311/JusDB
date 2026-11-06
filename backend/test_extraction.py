
from backend.app.extraction import extract_graph_from_chunk

from backend.app.graph_store import (
    verify_connection,
    save_graph,
    close_connection
)
sample_text = """
Python is a popular programming language.
Google uses Python for several internal tools.
Alice works at Google as a software engineer.
"""

chunk_id = "test_chunk_001"

try:
    graph = extract_graph_from_chunk(
        chunk_text=sample_text,
        chunk_id=chunk_id
    )

    print("\n========== EXTRACTED ENTITIES ==========")

    for entity in graph.entities:
        print("\nName:", entity.name)
        print("Type:", entity.entity_type.value)
        print("Description:", entity.description)
        print("Source:", entity.source_chunk_id)

    print("\n========== EXTRACTED RELATIONSHIPS ==========")

    for relation in graph.relations:
        print("\nSource:", relation.source)
        print("Target:", relation.target)
        print("Type:", relation.relation_type.value)
        print("Evidence:", relation.evidence_sentence)
        print("Chunk:", relation.evidence_chunk_id)

    print("\nExtraction completed successfully!")

except Exception as error:
    print("Extraction error:", error)

verify_connection()
save_graph(graph)
print("Extracted graph saved to Neo4j!")
close_connection()