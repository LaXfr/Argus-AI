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