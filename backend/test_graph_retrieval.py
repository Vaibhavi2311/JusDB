
from backend.app.graph_retrieval import (
    search_graph_entity,
    get_entity_relationships,
    multi_hop_search
)

from backend.app.graph_store import close_connection


try:

    print("\n========== ENTITY SEARCH ==========")

    entities = search_graph_entity(
        entity_name="Google",
        entity_type="ORGANIZATION"
    )

    for entity in entities:
        print(entity)


    print("\n========== DIRECT RELATIONSHIPS ==========")

    relationships = get_entity_relationships(
        entity_name="Google",
        entity_type="ORGANIZATION"
    )

    for relationship in relationships:
        print(relationship)


    print("\n========== MULTI-HOP SEARCH ==========")

    graph_results = multi_hop_search(
        entity_name="Google",
        entity_type="ORGANIZATION",
        max_hops=2
    )

    for result in graph_results:
        print(result)


finally:
    close_connection()
