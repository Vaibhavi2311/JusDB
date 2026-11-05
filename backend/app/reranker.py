from sentence_transformers import CrossEncoder

# Load the re-ranking model
reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_chunks(query, chunks, top_k=5):

    if not chunks:
        return []

    # Create question and chunk pairs
    pairs = [
        [query, chunk["text"]]
        for chunk in chunks
    ]

    # Calculate relevance scores
    scores = reranker.predict(pairs)

    # Attach scores to results
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    # Sort by relevance
    ranked_chunks = sorted(
        chunks,
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return ranked_chunks[:top_k]