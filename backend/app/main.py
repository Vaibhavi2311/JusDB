from fastapi import FastAPI

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