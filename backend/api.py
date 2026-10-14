import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag_pipeline import EnterpriseRAG
from evaluate import evaluate_single
from ingest import ingest_pdfs

app = FastAPI(title="Enterprise Hybrid RAG API")

# Enable CORS so your React frontend (localhost:5173) can talk to FastAPI (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the RAG pipeline once when the server starts (singleton QdrantClient instance)
rag = EnterpriseRAG(local_model="qwen2.5:3b")

class QueryRequest(BaseModel):
    question: str
    use_reranker: bool = True
    run_eval: bool = True

@app.get("/api/health")
def health_check():
    return {
        "status": "ok", 
        "model": rag.local_model,
        "collection": rag.collection,
        "db_path": str(rag.db_path)
    }

@app.post("/api/ingest")
def trigger_ingestion():
    """Trigger document ingestion using the shared QdrantClient singleton to avoid SQLite file locking."""
    try:
        chunks_count = ingest_pdfs(client=rag.qdrant)
        return {
            "status": "success",
            "message": f"Successfully ingested documents into Qdrant",
            "chunks_indexed": chunks_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/query")
def query_rag(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start_time = time.time()
    result, chunks = rag.query(req.question, use_reranker=req.use_reranker)
    latency_ms = round((time.time() - start_time) * 1000)

    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="No documents found in Qdrant or collection uninitialized. Run ingestion first."
        )

    # Calculate local Faithfulness & Context Precision if enabled and grounded
    metrics = None
    if req.run_eval and result.is_grounded and chunks:
        eval_res = evaluate_single(req.question, result.answer, chunks)
        metrics = {
            "faithfulness": eval_res.faithfulness_score,
            "context_precision": eval_res.context_precision_score,
            "reasoning": eval_res.reasoning
        }

    return {
        "answer": result.answer,
        "citations": result.citations,
        "verbatim_quotes": result.verbatim_quotes,
        "is_grounded": result.is_grounded,
        "chunks": chunks,
        "metrics": metrics,
        "latency_ms": latency_ms
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)