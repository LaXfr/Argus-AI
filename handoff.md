# Agent Handoff Specification: Enterprise Hybrid RAG

## 1. Project Context & Architecture
- **Objective:** Production-grade, 100% local, air-gapped Enterprise Hybrid RAG with Cross-Encoder reranking, local Ollama LLM structured outputs (Pydantic), quantitative local NLI evaluation, and a decoupled React (Vite) + FastAPI architecture.
- **Root Directory:** `enterprise-hybrid-rag/`
- **Environment:** Managed via `uv` in `.venv`.
- **Core Components:**
  - `backend/ingest.py`: PDF parsing via Docling, header chunking, dual vector indexing (Dense + BM25 Sparse) to local `./backend/qdrant_db`.
  - `backend/rag_pipeline.py`: Qdrant hybrid search, Cross-Encoder reranking (`BAAI/bge-reranker-base`), abstention guardrails, and Ollama (`qwen2.5:3b`) JSON schema generation.
  - `backend/evaluate.py`: Zero-cloud NLI cross-encoder computing Faithfulness and Context Precision.
  - `backend/api.py`: FastAPI REST API on port 8000 with CORS.
  - `frontend/`: React + Vite app on port 5173 talking to `http://localhost:8000/api/query`.

## 2. Active Execution Protocol
- **Execution Mode:** Batch all assigned tasks continuously. Do not stop after single-line edits or single file creations.
- **Doc Updates:** Every functional code change must be synchronized with `worklog.md`, `gitlog.md`, and `fixes.md`.
- **Validation Before Checkpoint:** Verify imports, endpoints, and build passes before yielding control.

## 3. Runtime Commands Reference
- **Activate Env:** `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
- **Check Ollama Model:** `ollama list` -> ensure `qwen2.5:3b` exists.
- **Run Ingestion:** `uv run python backend/ingest.py`
- **Run Backend:** `uv run uvicorn backend.api:app --reload --port 8000`
- **Run Frontend:** `cd frontend && npm run dev`
- **Lint / Build Check:** `cd frontend && npm run build`