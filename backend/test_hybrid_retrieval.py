
from backend.app.hybrid_retrieval import retrieve_hybrid_context
from backend.app.graph_store import close_connection


question = "What technologies does Google use?"

try:

    result = retrieve_hybrid_context(
        question=question,
        vector_limit=10,
        max_hops=2
    )

    print("\n========== QUESTION ==========")
    print(result["question"])

    print("\n========== VECTOR RESULTS ==========")

    for item in result["vector_results"]:
        print(item)

    print("\n========== GRAPH ENTITIES ==========")

    for entity in result["graph_entities"]:
        print(entity)

    print("\n========== GRAPH PATHS ==========")

    for path in result["graph_paths"]:
        print(path)

    print("\n========== COMBINED CONTEXT ==========")
    print(result["combined_context"])

finally:
    close_connection()
