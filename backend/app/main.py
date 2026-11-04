
from fastapi import FastAPI, UploadFile, File, HTTPException

from backend.app.ingestion import (
    extract_text_from_pdf,
    create_chunks
)

app = FastAPI(
    title="GraphRAG Enterprise Brain",
    description="AI-powered document intelligence system",
    version="1.0.0"
)


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

    # Check file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read uploaded PDF
    file_bytes = await file.read()

    # Check file size (10 MB maximum)
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

        # Extract text
        pages = extract_text_from_pdf(file_bytes)

        if not pages:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in PDF"
            )

        # Create chunks
        chunks = create_chunks(pages)

        return {
            "filename": file.filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "message": "PDF processed successfully",
            "chunks": chunks
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"PDF processing failed: {str(e)}"
        )
