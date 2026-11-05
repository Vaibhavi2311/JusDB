from pathlib import Path

from backend.app.celery_app import celery
from backend.app.ingestion import (
    extract_text_from_pdf,
    create_chunks
)
from backend.app.embeddings import generate_embeddings
from backend.app.vector_store import (
    create_collection,
    store_chunks
)


@celery.task(bind=True)
def process_pdf(self, file_path, filename):

    try:
        # Step 1: Update task status
        self.update_state(
            state="PROGRESS",
            meta={"step": "Reading PDF"}
        )

        # Step 2: Read the PDF
        pdf_path = Path(file_path)
        file_bytes = pdf_path.read_bytes()

        pages = extract_text_from_pdf(file_bytes)

        if not pages:
            raise ValueError(
                "No extractable text found in PDF"
            )

        # Step 3: Create chunks
        self.update_state(
            state="PROGRESS",
            meta={"step": "Creating text chunks"}
        )

        chunks = create_chunks(pages)

        if not chunks:
            raise ValueError("No text chunks were created")

        # Step 4: Generate embeddings
        self.update_state(
            state="PROGRESS",
            meta={"step": "Generating embeddings"}
        )

        texts = [
            chunk["text"] for chunk in chunks
        ]

        embeddings = generate_embeddings(texts)

        # Step 5: Store vectors in Qdrant
        self.update_state(
            state="PROGRESS",
            meta={"step": "Storing vectors in Qdrant"}
        )

        create_collection()

        stored_count = store_chunks(
            chunks,
            embeddings,
            filename
        )

        # Step 6: Return task result
        return {
            "filename": filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "stored_vectors": stored_count,
            "message": "PDF processed successfully"
        }

    except Exception as error:

        raise error