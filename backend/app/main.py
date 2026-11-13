
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app.graph_visualization import get_graph_visualization
from fastapi.middleware.cors import CORSMiddleware
from backend.app.graphrag_pipeline import ask_graphrag
from pydantic import BaseModel, Field
from backend.app.hybrid_retrieval import retrieve_hybrid_context
from backend.app.graph_retrieval import (
    search_graph_entity,
    get_entity_relationships,
    multi_hop_search
)
from pathlib import Path
from uuid import uuid4

# Project imports
from backend.app.celery_app import celery
from backend.app.tasks import process_pdf
from backend.app.reranker import rerank_chunks
from backend.app.llm import generate_answer
from backend.app.embeddings import generate_embedding

from backend.app.vector_store import (
    create_collection,
    search_hybrid_chunks
)


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024


# ==========================================
# REQUEST MODELS
# ==========================================

class ChatRequest(BaseModel):
    question: str


# ==========================================
# FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="GraphRAG Enterprise Brain",
    description="AI-powered document intelligence system",
    version="1.0.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# STARTUP EVENT
# ==========================================

@app.on_event("startup")
def startup_event():

    print("Initializing GraphRAG Enterprise Brain...")

    create_collection()

    print("Qdrant collection initialized successfully.")


# ==========================================
# HOME ENDPOINT
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Welcome to GraphRAG Enterprise Brain",
        "status": "running"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "application": "GraphRAG Enterprise Brain"
    }


# ==========================================
# PDF UPLOAD ENDPOINT
# ==========================================

@app.post("/documents/upload", status_code=202)
async def upload_document(file: UploadFile = File(...)):

    # Check filename and extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read at most 10 MB + 1 byte
    file_bytes = await file.read(MAX_FILE_SIZE + 1)

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(file_bytes) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File size must be below 10 MB"
        )

    saved_path = None

    try:

        # Sanitize filename
        safe_filename = Path(
            file.filename.replace("\\", "/")
        ).name

        # Generate unique filename
        saved_filename = f"{uuid4()}_{safe_filename}"

        saved_path = UPLOAD_DIR / saved_filename

        # Save PDF temporarily
        saved_path.write_bytes(file_bytes)

        # Submit background processing task
        task = process_pdf.delay(
            str(saved_path.resolve()),
            safe_filename
        )

        return {
            "message": "PDF uploaded. Processing started.",
            "job_id": task.id,
            "filename": safe_filename,
            "status": "QUEUED"
        }

    except Exception as e:

        # Remove saved file if task submission fails
        if saved_path and saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

    finally:

        await file.close()


# ==========================================
# HYBRID SEARCH + RERANKING
# ==========================================

@app.get("/search")
def search_documents(query: str):

    if not query.strip():

        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )

    try:

        # Step 1: Generate query embedding
        query_embedding = generate_embedding(query)

        # Step 2: Retrieve top 30 candidates
        candidates = search_hybrid_chunks(
            query_embedding,
            query,
            limit=30
        )

        # Step 3: Rerank candidates
        results = rerank_chunks(
            query,
            candidates,
            top_k=5
        )

        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


# ==========================================
# AI CHAT ENDPOINT
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:

        # Step 1: Generate question embedding
        query_embedding = generate_embedding(question)

        # Step 2: Retrieve relevant document chunks
        candidates = search_hybrid_chunks(
            query_embedding,
            question,
            limit=30
        )

        # Step 3: Rerank retrieved chunks
        results = rerank_chunks(
            question,
            candidates,
            top_k=5
        )

        # Step 4: Check search results
        if not results:

            return {
                "question": question,
                "answer": "No relevant documents found. Upload a PDF first.",
                "sources": []
            }

        # Step 5: Prepare document context
        context_parts = []

        for index, result in enumerate(results, start=1):

            context_parts.append(
                f"""
[Source {index}]
Filename: {result.get('filename', 'Unknown')}
Page: {result.get('page_number', 'Unknown')}
Content: {result.get('text', '')}
"""
            )

        context = "\n".join(context_parts)

        # Step 6: Generate AI answer
        answer = generate_answer(
            question,
            context
        )

        # Step 7: Return answer and sources
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


# ==========================================
# DOCUMENT PROCESSING STATUS
# ==========================================

@app.get("/documents/status/{job_id}")
def get_document_status(job_id: str):

    try:

        # Get Celery task result
        task_result = celery.AsyncResult(job_id)

        response = {
            "job_id": job_id,
            "status": task_result.state
        }

        # Task completed
        if task_result.state == "SUCCESS":

            response["result"] = task_result.result

        # Task failed
        elif task_result.state == "FAILURE":

            response["error"] = str(task_result.result)

        # Task is processing
        elif task_result.state == "PROGRESS":

            response["progress"] = task_result.info

        return response

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve task status: {str(e)}"
        )
class GraphSearchRequest(BaseModel):
    entity_name: str
    entity_type: str
    max_hops: int = Field(default=2, ge=1, le=3)
    
    
@app.get("/graph/entity")
def graph_entity_search(
    entity_name: str,
    entity_type: str
):
    return {
        "results": search_graph_entity(
            entity_name,
            entity_type
        )
    }


@app.get("/graph/relationships")
def graph_relationship_search(
    entity_name: str,
    entity_type: str
):
    return {
        "results": get_entity_relationships(
            entity_name,
            entity_type
        )
    }


@app.post("/graph/multi-hop")
def graph_multi_hop(request: GraphSearchRequest):

    return {
        "entity": request.entity_name,
        "max_hops": request.max_hops,
        "results": multi_hop_search(
            request.entity_name,
            request.entity_type,
            request.max_hops
        )
    }

@app.get("/chat/retrieve")
def hybrid_retrieval_endpoint(question: str):

    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    result = retrieve_hybrid_context(
        question=question,
        vector_limit=10,
        max_hops=2
    )

    return {
        "question": result["question"],
        "vector_results": result["vector_results"],
        "graph_entities": result["graph_entities"],
        "graph_paths": result["graph_paths"],
        "combined_context": result["combined_context"]
    }

@app.get("/graphrag/ask")
def graphrag_ask(question: str):

    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        result = ask_graphrag(question)

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"GraphRAG processing failed: {str(error)}"
        )

@app.get("/graph/visualization")
def graph_visualization_endpoint(
    entity_name: str,
    entity_type: str,
    limit: int = 100
):
    if not entity_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Entity name cannot be empty"
        )

    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 200"
        )

    try:
        return get_graph_visualization(
            entity_name=entity_name,
            entity_type=entity_type,
            limit=limit
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve graph visualization"
        )
