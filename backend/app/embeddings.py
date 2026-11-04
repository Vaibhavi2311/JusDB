from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text):
    """
    Convert text into a numerical vector.
    """
    embedding = model.encode(text)

    return embedding.tolist()


def generate_embeddings(texts):
    """
    Convert multiple text chunks into vectors.
    """
    embeddings = model.encode(texts)

    return embeddings.tolist()