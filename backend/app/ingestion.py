
from io import BytesIO
import re

from pypdf import PdfReader
import tiktoken


# Tokenizer
encoding = tiktoken.get_encoding("cl100k_base")


# Step 1: Extract text from PDF
def extract_text_from_pdf(file_bytes):

    pdf = PdfReader(BytesIO(file_bytes))

    pages = []

    for page_number, page in enumerate(pdf.pages, start=1):

        text = page.extract_text() or ""

        # Clean extracted text
        text = clean_text(text)

        if text.strip():
            pages.append({
                "page_number": page_number,
                "text": text
            })

    return pages


# Step 2: Clean extracted text
def clean_text(text):

    # Replace multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)

    # Remove unwanted characters
    text = text.strip()

    return text


# Step 3: Divide text into chunks
def create_chunks(pages, chunk_size=500, overlap=80):

    chunks = []

    chunk_id = 0

    for page in pages:

        text = page["text"]

        # Convert text into tokens
        tokens = encoding.encode(text)

        start = 0

        while start < len(tokens):

            end = min(start + chunk_size, len(tokens))

            # Extract chunk tokens
            chunk_tokens = tokens[start:end]

            # Convert tokens back to text
            chunk_text = encoding.decode(chunk_tokens)

            chunks.append({
                "chunk_id": chunk_id,
                "page_number": page["page_number"],
                "text": chunk_text,
                "token_count": len(chunk_tokens)
            })

            chunk_id += 1

            # Move forward with overlap
            start += chunk_size - overlap

    return chunks
