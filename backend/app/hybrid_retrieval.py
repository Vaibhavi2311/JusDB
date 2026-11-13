
from backend.app.embeddings import generate_embedding

from backend.app.query_entity_extraction import (
    extract_query_entities
)

from backend.app.graph_retrieval import (
    search_graph_entity,
    multi_hop_search
)

from backend.app.vector_store import search_hybrid_chunks


# ==========================================
# REMOVE DUPLICATE TEXT
# ==========================================

def remove_duplicate_text(items):

    unique_items = []
    seen = set()

    for item in items:

        cleaned = item.strip()
        normalized = cleaned.lower()

        if normalized and normalized not in seen:

            seen.add(normalized)
            unique_items.append(cleaned)

    return unique_items


# ==========================================
# HYBRID RETRIEVAL
# ==========================================

def retrieve_hybrid_context(
    question: str,
    vector_limit: int = 10,
    max_hops: int = 2
):

    # 1. Generate question embedding
    query_embedding = generate_embedding(question)

    # 2. Retrieve document chunks from Qdrant
    vector_results = search_hybrid_chunks(
        query_embedding=query_embedding,
        query=question,
        limit=vector_limit
    )

    # 3. Extract entities from question
    query_entities = extract_query_entities(question)

    graph_entities = []
    graph_paths = []

    # 4. Search entities in Neo4j
    for entity in query_entities.entities:

        entity_type = entity.entity_type.value

        entity_results = search_graph_entity(
            entity.name,
            entity_type
        )

        graph_entities.extend(entity_results)

        # 5. Multi-hop graph search
        if entity_results:

            paths = multi_hop_search(
                entity.name,
                entity_type,
                max_hops=max_hops
            )

            graph_paths.extend(paths)

    # 6. Build vector context
    vector_context = []

    for item in vector_results:

        text = item.get("text", "")

        if text:
            vector_context.append(text)

    # 7. Build graph context
    graph_context = []

    for path in graph_paths:

        for entity in path.get("entities", []):

            graph_context.append(
                f"Entity: {entity.get('name')} "
                f"Type: {entity.get('type')} "
                f"Description: {entity.get('description', '')}"
            )

        for relation in path.get("relationships", []):

            graph_context.append(
                f"Relationship: {relation.get('type')}. "
                f"Evidence: {relation.get('evidence', '')}. "
                f"Source chunk: "
                f"{relation.get('evidence_chunk_id', '')}"
            )

    # 8. Remove duplicate context
    vector_context = remove_duplicate_text(vector_context)
    graph_context = remove_duplicate_text(graph_context)

    # 9. Combine both contexts
    combined_context = (
        "DOCUMENT EVIDENCE:\n"
        + "\n".join(vector_context)
        + "\n\nGRAPH EVIDENCE:\n"
        + "\n".join(graph_context)
    )

    return {
        "question": question,
        "vector_results": vector_results,
        "graph_entities": graph_entities,
        "graph_paths": graph_paths,
        "combined_context": combined_context
    }
