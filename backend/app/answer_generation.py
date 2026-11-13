
import ollama

from pydantic import BaseModel, Field


MODEL_NAME = "llama3.2:3b"


class GeneratedAnswer(BaseModel):
    answer: str
    supported: bool
    sources: list[str] = Field(default_factory=list)


def generate_answer(
    question: str,
    context: str
) -> GeneratedAnswer:

    if not context.strip():
        return GeneratedAnswer(
            answer=(
                "I could not find sufficient evidence "
                "in the uploaded documents or knowledge graph."
            ),
            supported=False,
            sources=[]
        )

    prompt = f"""
You are an enterprise document question-answering assistant.

Answer the user's question using ONLY the evidence
provided below.

RULES:
1. Do not invent facts.
2. Do not use outside knowledge.
3. If evidence is insufficient, say so clearly.
4. Keep the answer clear and concise.
5. Mention the source chunk IDs when they are available.
6. Do not claim that a source supports something it does not.
7. Return valid JSON only.

Required JSON format:

{{
    "answer": "Your answer here",
    "supported": true,
    "sources": ["chunk_001"]
}}

If the evidence is insufficient, use supported=false
and explain that the evidence is insufficient.

QUESTION:
{question}

EVIDENCE:
{context}
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

    content = response.message.content

    return GeneratedAnswer.model_validate_json(content)
