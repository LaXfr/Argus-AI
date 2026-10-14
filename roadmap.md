# Project Roadmap & Implementation Milestones

## Phase 1: Environment & Foundation Setup
- [x] Scaffold project directory structure (`backend/`, `frontend/`, `data/`).
- [x] Initialize virtual environment via `uv` and install core backend dependencies.
- [x] Configure Ollama locally with `qwen2.5` model weights.
- [x] Scaffold React frontend using Vite.

## Phase 2: Ingestion & Storage Pipeline
- [x] Place sample PDF documents into `backend/data/` (`enterprise_platform_spec.pdf` & `.md`).
- [x] Execute `backend/ingest.py` and verify local disk persistence in `backend/qdrant_db/`.
- [x] Validate both dense embeddings (`bge-small-en-v1.5`) and sparse indices (`bm25`) are created in Qdrant collections.

## Phase 3: Core RAG Pipeline & Evaluation Logic
- [x] Test standalone query execution in `backend/rag_pipeline.py` via Python test scripts.
- [x] Verify Cross-Encoder reranker score output and abstention thresholding (sigmoid normalized).
- [x] Validate Ollama Pydantic JSON schema generation (`RAGResponse` model validation).
- [x] Test local math-based evaluation metric calculation (`backend/evaluate.py`).

## Phase 4: Full-Stack Integration & API
- [x] Start FastAPI backend (`backend/api.py`) and verify `/api/health` and `/api/query` endpoints.
- [x] Verify CORS headers allow browser requests from `http://localhost:5173`.
- [x] Connect React frontend state to API responses; verify loading, success, and error states.
- [x] Test collapsible chunk inspection, latency counters, and metric score cards in UI.

## Phase 5: Verification & Polish
- [x] Create automated end-to-end benchmark script (`backend/benchmark.py`) comparing Reranked vs. Non-Reranked outputs.
- [x] Write production-ready `README.md` containing architecture diagrams and benchmark comparison tables.
- [x] Perform full dry run from empty ingestion state to complete web UI query.