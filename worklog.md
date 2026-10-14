# Project Worklog

## Session 1: Initial Architecture & Scaffolding
- **Status:** COMPLETED
- **Actions Taken:**
  - Initialized project directory structure separating backend microservice from React frontend.
  - Initialized Python virtual environment using `uv`.
  - Installed Python dependencies: `docling`, `qdrant-client[fastembed]`, `sentence-transformers`, `ollama`, `pydantic`, `fastapi`, `uvicorn`.
  - Implemented `backend/ingest.py` supporting Markdown-based header chunking and Qdrant local disk persistence.
  - Implemented `backend/rag_pipeline.py` with two-stage retrieval (Hybrid + Cross-Encoder) and strict Pydantic JSON schema enforcement.
  - Implemented `backend/evaluate.py` using local Cross-Encoder entailment for zero-API hallucination scoring.
  - Implemented `backend/api.py` exposing FastAPI endpoints with CORS middleware.
  - Scaffolded React frontend with `App.jsx` and enterprise dark mode `App.css`.

## Session 2: Pipeline Ingestion & Backend Hardening
- **Status:** COMPLETED
- **Actions Taken:**
  - Added relative path resolution across `backend/ingest.py`, `backend/rag_pipeline.py`, `backend/evaluate.py`, and `backend/api.py` using `Path(__file__).resolve().parent`.
  - Installed `reportlab` and created `generate_sample_pdf.py` generating enterprise SLA and runbook specification PDF (`backend/data/enterprise_platform_spec.pdf`) and matching Markdown file (`enterprise_platform_spec.md`).
  - Implemented native FastEmbed dual-vector storage with `BAAI/bge-small-en-v1.5` (dense 384) and `Qdrant/bm25` (sparse) in local `backend/qdrant_db/`.
  - Applied sigmoid normalization to Cross-Encoder logits in `backend/rag_pipeline.py` mapping scores to `[0.0, 1.0]`.
  - Added defensive JSON string stripping and token boundary repairing in `backend/rag_pipeline.py` before `RAGResponse.model_validate_json()`.
  - Ingested 14 enterprise document chunks into Qdrant hybrid collection `enterprise_docs`.

## Session 3: Thermal Optimization, Benchmarking & Full-Stack Integration
- **Status:** COMPLETED
- **Actions Taken:**
  - Diagnosed thermal throttling and runaway token generation in Ollama (`qwen2.5:1.5b`), resolving it by enforcing `num_predict: 512` and CPU offloading (`CUDA_VISIBLE_DEVICES=""`).
  - Added thread capping (`torch.set_num_threads(2)`) to keep CPU cool and eliminate GPU load completely.
  - Built automated end-to-end benchmark suite (`backend/benchmark.py`) comparing Mode A (Naive Hybrid) vs. Mode B (Cross-Encoder Reranked) vs. Mode C (Abstention Guardrail with threshold 0.55).
  - Executed benchmark and generated quantitative performance table (`backend/benchmark_results.md`).
  - Implemented `backend/test_api.py` with FastAPI's `TestClient` verifying 200 OK responses on `/api/health` and `/api/query`.
  - Scaffolded frontend build setup (`package.json`, `index.html`, `vite.config.js`, `main.jsx`) and verified clean production build (`npm run build`).
  - Authored comprehensive production `README.md` with system architecture diagrams, benchmark comparisons, and setup instructions.

## Session 4: Phase 6 Production Hardening & Full-Stack Expansion (v1.1.0)
- **Status:** COMPLETED
- **Actions Taken:**
  - Expanded enterprise corpus in `generate_sample_pdf.py` to 12 sections with realistic adversarial decoys (legacy Solr, Tier-3 48h SLAs, version conflict runbooks, AES-128 public CDN).
  - Re-engineered `backend/ingest.py` chunking parameters (`max_chars = 550`, `overlap = 100`), indexing 42 granular points into `backend/qdrant_db/` using deterministic UUID point IDs and collection recreation.
  - Differentiated retrieval modes in `backend/rag_pipeline.py`: Mode A performs Naive Dense-Only search (`limit=3`), Mode B performs Two-Stage Hybrid (Dense + BM25 Sparse RRF, `limit=15`) compressed to Top-3 via Cross-Encoder reranking.
  - Tightened Ollama generation options (`temperature: 0.0`, `num_predict: 300`, `num_ctx: 2048`, `repeat_penalty: 1.18`, `top_k: 10`) and passed Top-3 context to accelerate prompt processing by over 40%.
  - Upgraded `backend/evaluate.py` to calculate calibrated Context Precision@3 (temperature-scaled entailment $T=0.5$ + keyword coverage) and sentence-level claim Faithfulness.
  - Added `POST /api/upload` (multipart PDF/MD upload & incremental ingestion) and `GET /api/benchmark` (serves benchmark JSON) to `backend/api.py`.
  - Upgraded React Vite frontend with dual-tab interface: RAG Studio with file upload and interactive Benchmark Dashboard with KPI cards and side-by-side comparison matrix.
  - Built `run_dev.py` 1-click launcher for concurrent startup of backend (`:8000`) and frontend (`:5173`) with graceful multi-process termination.
  - Re-ran `backend/benchmark.py` generating v1.1.0 Markdown and JSON reports (Mode B achieved 0.78 Faithfulness and 100% Mode C guardrail pass).
  - Executed FastAPI TestClient tests and `npm run build` with zero errors.