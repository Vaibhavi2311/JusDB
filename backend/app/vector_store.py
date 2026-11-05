import re
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)
from rank_bm25 import BM25Okapi


client = QdrantClient(
    url="http://localhost:6333"
)

COLLECTION_NAME = "document_chunks"


def create_collection():

    collections = client.get_collections().collections

    existing_names = [
        collection.name for collection in collections
    ]

    if COLLECTION_NAME not in existing_names:

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

        print("Collection created successfully!")

    else:
        print("Collection already exists!")


def store_chunks(chunks, embeddings, filename):

    points = []

    for chunk, embedding in zip(chunks, embeddings):

        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "filename": filename,
                "page_number": chunk["page_number"],
                "text": chunk["text"],
                "token_count": chunk["token_count"]
            }
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)


def tokenize(text):

    return re.findall(
        r"\b\w+\b",
        text.lower()
    )


def get_all_points():

    all_points = []
    offset = None

    while True:

        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        all_points.extend(points)

        if next_offset is None:
            break

        offset = next_offset

    return all_points


def search_hybrid_chunks(query_embedding, query, limit=5):

    # 1. Vector search
    vector_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=30,
        with_payload=True
    ).points

    # 2. Get stored text for BM25
    all_points = get_all_points()

    if not all_points:
        return []

    documents = [
        tokenize(point.payload.get("text", ""))
        for point in all_points
    ]

    # 3. BM25 keyword search
    bm25 = BM25Okapi(documents)

    query_tokens = tokenize(query)

    bm25_scores = bm25.get_scores(query_tokens)

    bm25_ranked_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True
    )

    # 4. Reciprocal Rank Fusion
    rrf_scores = {}
    point_data = {}

    rrf_k = 60

    # Add vector rankings
    for rank, result in enumerate(vector_results, start=1):

        point_id = str(result.id)

        rrf_scores[point_id] = (
            rrf_scores.get(point_id, 0)
            + 1 / (rrf_k + rank)
        )

        point_data[point_id] = {
            "id": point_id,
            "filename": result.payload.get("filename"),
            "page_number": result.payload.get("page_number"),
            "text": result.payload.get("text"),
            "vector_score": result.score,
            "bm25_score": 0
        }

    # Add BM25 rankings
    for rank, index in enumerate(
        bm25_ranked_indices[:30],
        start=1
    ):

        point = all_points[index]
        point_id = str(point.id)

        rrf_scores[point_id] = (
            rrf_scores.get(point_id, 0)
            + 1 / (rrf_k + rank)
        )

        if point_id not in point_data:

            point_data[point_id] = {
                "id": point_id,
                "filename": point.payload.get("filename"),
                "page_number": point.payload.get("page_number"),
                "text": point.payload.get("text"),
                "vector_score": None,
                "bm25_score": bm25_scores[index]
            }

        else:

            point_data[point_id]["bm25_score"] = (
                bm25_scores[index]
            )

    # 5. Sort using combined RRF scores
    ranked_results = sorted(
        point_data.values(),
        key=lambda item: rrf_scores[item["id"]],
        reverse=True
    )

    for result in ranked_results:
        result["rrf_score"] = rrf_scores[result["id"]]

    return ranked_results[:limit]