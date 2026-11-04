
from fastapi import FastAPI, UploadFile, File, HTTPException

from backend.app.ingestion import (
    extract_text_from_pdf,
    create_chunks
)
from backend.app.embeddings import generate_embedding, generate_embeddings
from backend.app.vector_store import (
    create_collection,
    store_chunks,
    search_chunks
)

    
app = FastAPI(
    title="GraphRAG Enterprise Brain",
    description="AI-powered document intelligence system",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    create_collection()
    
@app.get("/")
def home():

    return {
        "message": "Welcome to GraphRAG Enterprise Brain"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must be below 10 MB"
        )

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:
        pages = extract_text_from_pdf(file_bytes)

        if not pages:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in PDF"
            )

        chunks = create_chunks(pages)

        texts = [chunk["text"] for chunk in chunks]

        embeddings = generate_embeddings(texts)

        stored_count = store_chunks(
            chunks,
            embeddings,
            file.filename
        )

        return {
            "filename": file.filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "stored_vectors": stored_count,
            "message": "PDF processed and stored successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
@app.get("/search")
def search_documents(query: str):

    query_embedding = generate_embedding(query)

    results = search_chunks(
        query_embedding,
        limit=5
    )

    return {
        "query": query,
        "results": results
    }