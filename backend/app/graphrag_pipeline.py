
from backend.app.hybrid_retrieval import (
    retrieve_hybrid_context
)

from backend.app.answer_generation import (
    generate_answer
)


def collect_source_ids(data):
    """Collect chunk IDs that exist in retrieved evidence."""

    source_ids = set()

    def scan(value):
        if isinstance(value, dict):
            for key, item in value.items():

                if key in (
                    "chunk_id",
                    "source_chunk_id",
                    "evidence_chunk_id"
                ):
                    if item is not None:
                        source_ids.add(str(item))

                scan(item)

        elif isinstance(value, list):
            for item in value:
                scan(item)

    scan(data)

    return source_ids


def ask_graphrag(question: str):

    retrieval = retrieve_hybrid_context(
        question=question,
        vector_limit=10,
        max_hops=2
    )

    context = retrieval.get(
        "combined_context",
        ""
    )

    generated = generate_answer(
        question=question,
        context=context
    )

    # Only retain citations found in retrieved evidence
    allowed_sources = collect_source_ids(retrieval)

    verified_sources = [
        source
        for source in generated.sources
        if source in allowed_sources
    ]

    return {
        "question": question,
        "answer": generated.answer,
        "supported": generated.supported,
        "sources": verified_sources,
        "vector_results": retrieval.get(
            "vector_results", []
        ),
        "graph_entities": retrieval.get(
            "graph_entities", []
        ),
        "graph_paths": retrieval.get(
            "graph_paths", []
        )
    }
