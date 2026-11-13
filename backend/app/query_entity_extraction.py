
import json
import ollama

from pydantic import BaseModel, Field
from backend.app.graph_schema import EntityType


class QueryEntity(BaseModel):
    name: str = Field(min_length=1)
    entity_type: EntityType


class QueryEntities(BaseModel):
    entities: list[QueryEntity] = Field(default_factory=list)


MODEL_NAME = "llama3.2:3b"


def extract_query_entities(question: str) -> QueryEntities:

    prompt = f"""
    Identify named entities in the user's question.

    Allowed entity types:
    PERSON, ORGANIZATION, PROJECT, TECHNOLOGY,
    CONCEPT, LOCATION, DOCUMENT, DATE.

    Return valid JSON only in this format:

    {{
        "entities": [
            {{
                "name": "Google",
                "entity_type": "ORGANIZATION"
            }}
        ]
    }}

    Do not invent entities.
    If no entities are found, return an empty list.

    QUESTION:
    {question}
    """

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

    data = json.loads(response.message.content)

    return QueryEntities.model_validate(data)
