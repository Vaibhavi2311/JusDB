
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.app.llm import generate_answer
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
class ChatRequest(BaseModel):
    question: str
    
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
@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        # Step 1: Convert question into embedding
        query_embedding = generate_embedding(question)

        # Step 2: Retrieve relevant chunks from Qdrant
        results = search_chunks(
            query_embedding,
            limit=5
        )

        if not results:
            return {
                "question": question,
                "answer": "No relevant documents found. Upload a PDF first.",
                "sources": []
            }

        # Step 3: Prepare context for the LLM
        context_parts = []

        for index, result in enumerate(results, start=1):

            context_parts.append(
                f"""
[Source {index}]
Filename: {result['filename']}
Page: {result['page_number']}
Content: {result['text']}
"""
            )

        context = "\n".join(context_parts)

        # Step 4: Generate answer
        answer = generate_answer(
            question,
            context
        )

        # Step 5: Return answer and references
        return {
            "question": question,
            "answer": answer,
            "sources": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )