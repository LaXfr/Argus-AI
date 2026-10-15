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

## Session 5: Phase 7 Retrieval Separation, Singleton Caching & Release v1.2.0
- **Status:** COMPLETED
- **Actions Taken:**
  - Diagnosed double-sigmoid score compression issue where `bge-reranker-base` raw output in `[0.0, 1.0]` was mapped to `0.5000` for out-of-domain queries. Removed redundant sigmoid, preserving true probabilities (`0.0001` for out-of-domain).
  - Discovered that identical duplicate chunks between `enterprise_platform_spec.pdf` and `.md` occupied ranks 1 and 2 in naive search. Separated corpus into authoritative primary PDF (`enterprise_platform_spec.pdf`) and distinct decoy Markdown (`legacy_and_decoy_systems.md`), eliminating duplicate points.
  - Implemented true Mode A vs Mode B differentiation in `rag_pipeline.py`: Mode A reflects naive retrieval with distractor contamination (0.60 Precision@3), whereas Mode B uses Hybrid RRF + Cross-Encoder reranking to achieve 0.90 Precision@3 (+47.9% boost) and 1.00 Faithfulness.
  - Cached `CrossEncoder("BAAI/bge-reranker-base")` as a module-level shared singleton `get_shared_cross_encoder()` across `rag_pipeline.py` and `evaluate.py`, eliminating duplicate model loading and cutting process RAM by 50%.
  - Defaulted fast inference model to `qwen2.5:1.5b` with tightened generation parameters (`num_predict: 180`, `num_ctx: 1024`).
  - Executed automated benchmark suite `backend/benchmark.py`, generating v1.2.0 Markdown and JSON reports.
  - Verified 100% pass rate in `backend/test_api.py` and `cd frontend && npm run build` (596ms).

## Session 6: Phase 8 Production UI Overhaul (Linear / Vercel / Raycast Obsidian Aesthetic) & Release v1.3.0
- **Status:** COMPLETED
- **Actions Taken:**
  - Integrated Google Fonts `Inter` (prose & UI) and `JetBrains Mono` (code, latency, metrics, citations) in `frontend/index.html`.
  - Re-architected `frontend/src/App.jsx` with enterprise-grade UI structure:
    - Fixed top glass navbar with 4-quadrant geometric logo, `v1.3` pill, segmented tab pill switcher (`RAG Workbench` vs. `Evaluation Benchmarks`), and live telemetry pills (`Air-Gapped Local`, `Qdrant RRF + BGE`, `Qwen 2.5:1.5b`).
    - Hero command input card with search icon, white primary CTA button (`Run Pipeline ↵`) with spinner & timer, and 4 quick preset query chips (`ERR-409-TIMEOUT`, `Tier-1 SLA Targets`, `Zero-Trust Encryption`, `Abstention Guardrail`).
    - iOS-style toggle switches for Cross-Encoder Reranker and Live NLI Entailment Judge, plus collapsible document ingestion drawer.
    - Shimmer keyframe animated pulsing skeleton loader preventing cumulative layout shift during Ollama inference.
    - Asymmetric 2-column results workspace (60% synthesis & evaluation / 40% retrieval inspection).
    - Left column: Grounded vs. Abstained status badge, latency tag, verified chunk citations stream, verbatim quotes with emerald border accent, and animated NLI evaluation gauges (Faithfulness & Context Precision@3).
    - Right column: Retrieved context chunks stream with rank tags (`#1`, `#2`, `#3`), dual score visualizer bars (`Rerank` vs. `RRF Fusion`), source metadata, and verbatim text box.
    - Evaluation Benchmarks dashboard: 3 hero KPI bento cards (`+47.9%` Precision lift, 100% Faithfulness, 100% Guardrail pass), comparative matrix table with mini score progress bars and overall mean footer, and Mode C guardrail card.
  - Implemented complete stylesheet in `frontend/src/App.css` featuring `#050507` obsidian background with radial ambient glow, elevated translucent surfaces (`rgba(10, 10, 14, 0.75)` with `backdrop-filter: blur(16px)`), hairline borders (`rgba(255, 255, 255, 0.07)`), emerald/rose/indigo status accents, and responsive layout for desktop/tablet/mobile.
  - Successfully executed `npm run build` in `frontend/`, verifying 0 errors and 0 warnings (480ms build time).

## Session 7: Failed to Fetch Root Cause Resolution & Unified Launcher Hardening (Release v1.3.1)
- **Status:** COMPLETED
- **Actions Taken:**
  - Diagnosed `Failed to fetch` root cause: frontend called hardcoded `http://localhost:8000` encountering Windows IPv6 `localhost` vs `127.0.0.1` binding divergence, while orphaned background python processes held locks on `qdrant_db` and port 8000.
  - Configured Vite `server.proxy` for `'/api': { target: 'http://127.0.0.1:8000', changeOrigin: true }` in `frontend/vite.config.js`.
  - Implemented `apiFetch` in `frontend/src/App.jsx` using relative endpoints (`/api/query`, `/api/upload`, `/api/benchmark`, `/api/health`) with automatic fallback to `127.0.0.1:8000`. Added live backend connection polling and visual status in the navbar telemetry pill.
  - Hardened `run_dev.py`:
    - Explicitly resolves virtual environment interpreter (`.venv/Scripts/python.exe` on Windows).
    - Spawns backend with `--host 127.0.0.1 --port 8000`.
    - Detects and terminates stale orphan processes holding port 8000.
    - Polls `http://127.0.0.1:8000/api/health` until 200 OK before printing ready banner.
    - Uses OS process tree termination (`taskkill /F /T`) on shutdown to prevent leaked worker processes.
  - Cleaned up stale processes and verified `GET /api/health`, `GET /api/benchmark`, and `POST /api/query` return 200 OK cleanly.
  - Rebuilt production bundle (`npm run build`) in 1.35s with 0 errors.