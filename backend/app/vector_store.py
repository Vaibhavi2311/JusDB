from qdrant_client import QdrantClient
from uuid import uuid4
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

# Connect to local Qdrant
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

def search_chunks(query_embedding, limit=5):

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=limit,
        with_payload=True
    ).points

    return [
        {
            "score": result.score,
            "filename": result.payload["filename"],
            "page_number": result.payload["page_number"],
            "text": result.payload["text"]
        }
        for result in results
    ]