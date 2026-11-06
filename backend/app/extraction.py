
import json
import ollama

from pydantic import ValidationError

from backend.app.graph_schema import (
    Entity,
    Relation,
    ExtractedGraph
)

from backend.app.extraction_prompt import EXTRACTION_PROMPT


MODEL_NAME = "llama3.2:3b"


def extract_graph_from_chunk(
    chunk_text: str,
    chunk_id: str,
    max_retries: int = 2
) -> ExtractedGraph:

    if not chunk_text.strip():
        raise ValueError("Chunk text cannot be empty")

    prompt = EXTRACTION_PROMPT.format(
        chunk_text=chunk_text
    )

    for attempt in range(max_retries + 1):

        try:
            response = ollama.chat(
                model=MODEL_NAME,
                format="json",
                options={"temperature": 0},
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            response_text = response.message.content

            # Convert JSON text into a Python dictionary
            data = json.loads(response_text)

            # Add source chunk IDs to every entity
            for entity in data.get("entities", []):
                entity["source_chunk_id"] = chunk_id

            # Add evidence chunk IDs to every relationship
            for relation in data.get("relations", []):
                relation["evidence_chunk_id"] = chunk_id

            # Validate the extracted data
            extracted_graph = ExtractedGraph.model_validate(data)

            # Ensure relationship endpoints exist
            entity_names = {
                entity.name.strip().lower()
                for entity in extracted_graph.entities
            }

            for relation in extracted_graph.relations:
                if relation.source.strip().lower() not in entity_names:
                    raise ValueError(
                        f"Unknown relationship source: {relation.source}"
                    )

                if relation.target.strip().lower() not in entity_names:
                    raise ValueError(
                        f"Unknown relationship target: {relation.target}"
                    )

            return extracted_graph

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError
        ) as error:

            print(
                f"Extraction attempt {attempt + 1} failed: {error}"
            )

            if attempt == max_retries:
                raise ValueError(
                    "Could not extract valid graph data"
                ) from error

    raise ValueError("Extraction failed")
