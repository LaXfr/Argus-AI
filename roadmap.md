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

## Phase 5: Verification & Initial Polish
- [x] Create automated end-to-end benchmark script (`backend/benchmark.py`) comparing Reranked vs. Non-Reranked outputs.
- [x] Write production-ready `README.md` containing architecture diagrams and benchmark comparison tables.
- [x] Perform full dry run from empty ingestion state to complete web UI query.

## Phase 6: Production Hardening, Benchmark Calibration & Full-Stack Expansion (v1.1.0)
- [x] Expand toy corpus to 42 granular chunks (550 chars, 100 overlap) with 12 sections including adversarial distractors (legacy Solr, Tier-3 48h RTO, conflicting version runbooks, public CDN encryption).
- [x] Differentiate retrieval modes: Mode A = Pure Dense Vector Search (`top_k=3`); Mode B = Production Two-Stage Hybrid (Dense + BM25 RRF, `limit=15`) compressed to Top-3 via Cross-Encoder reranking; Mode C = Abstention Guardrail (`threshold=0.55`).
- [x] Calibrate evaluation metrics in `backend/evaluate.py`: Context Precision@3 (temperature-scaled entailment $T=0.5$ + query keyword recall) and sentence-level claim Faithfulness.
- [x] Optimize Ollama latency without thermal runaway: enforce strict generation bounds (`num_predict: 300`, `num_ctx: 2048`, `repeat_penalty: 1.18`, `top_k: 10`, `temperature: 0.0`), Top-3 prompt context, and CPU thread capping (`torch.set_num_threads(4)`).
- [x] Add live multipart file upload (`POST /api/upload`) with incremental Qdrant upserts and benchmark results API (`GET /api/benchmark`).
- [x] Upgrade React Vite frontend with dual-tab interface: RAG Studio with file upload and interactive Benchmark Dashboard with KPI cards and side-by-side comparison matrix.
- [x] Re-run automated benchmark suite, verify 100% guardrail pass and production metrics, and build `run_dev.py` 1-click launcher.

## Phase 7: Retrieval Differentiation, Singleton Optimization & Release v1.2.0
- [x] Eliminate redundant sigmoid compression: `bge-reranker-base` raw output is recognized and used as an exact probability in `[0.0, 1.0]`, allowing out-of-domain queries to display their true probability (`0.0001`) instead of an artificial `0.5000`.
- [x] True Mode A vs Mode B separation: Mode A demonstrates real-world semantic distractor contamination in un-reranked dense search (`0.60` Precision@3), while Mode B filters out all distractors via Cross-Encoder reranking (`0.90` Precision@3), achieving a verified **+47.9% Precision boost**.
- [x] Memory & Process Optimization: Implemented shared module-level singleton `get_shared_cross_encoder()` across `rag_pipeline.py` and `evaluate.py`, loading weights into RAM exactly once.
- [x] Default fast inference model to `qwen2.5:1.5b` with tightened generation limits (`num_predict: 180`, `num_ctx: 1024`) for fast CPU response times.
- [x] Expanded `backend/test_api.py` covering health, benchmark, query with evaluation, and 400 validation (100% pass).
- [x] Re-verified frontend Vite bundle (`npm run build` completed cleanly in 596ms).