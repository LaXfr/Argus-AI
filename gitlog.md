# Git Commit History & Release Log

## [Release v1.3.1] - Runtime Fix: Vite Proxy, Venv Resolution & Launcher Health Polling
- `fix(vite)`: Configure server.proxy for '/api' -> 'http://127.0.0.1:8000' in frontend/vite.config.js to eliminate Windows localhost IPv6 and CORS preflight blocks
- `fix(frontend)`: Implement apiFetch in frontend/src/App.jsx with relative endpoints (/api/query, /api/upload, /api/benchmark, /api/health) and automatic fallback to 127.0.0.1:8000
- `feat(frontend)`: Add live backend connection monitoring and offline indicator in navbar telemetry pill
- `fix(launcher)`: Ensure run_dev.py explicitly resolves virtual environment Python interpreter (.venv/Scripts/python.exe) and binds to 127.0.0.1:8000
- `fix(launcher)`: Add pre-flight stale process detection and termination for port 8000 to prevent Qdrant SQLite lock crashes
- `fix(launcher)`: Add health polling on http://127.0.0.1:8000/api/health blocking until 200 OK before displaying active services banner
- `fix(launcher)`: Implement process tree termination (taskkill /F /T) on Ctrl+C to prevent orphaned worker processes
- `test(runtime)`: Verify live 200 OK responses on GET /api/health, GET /api/benchmark, and POST /api/query
- `test(build)`: Verify frontend production bundle via npm run build (1.35s, 0 errors)
- `docs(release)`: Update fixes.md, worklog.md, and gitlog.md for Release v1.3.1

---

## [Release v1.3.0] - Phase 8 Production UI Overhaul (Linear / Vercel / Raycast Obsidian Aesthetic)
- `feat(ui)`: Overhaul React frontend styling to Linear / Vercel Geist / Raycast obsidian aesthetic (`#050507` canvas, ambient glow, translucent glass cards)
- `feat(typography)`: Integrate Google Fonts `Inter` for prose and `JetBrains Mono` for latency, citations, codes, and scores
- `feat(navbar)`: Implement sticky glass navbar with 4-quadrant geometric SVG logo, `v1.3` pill, segmented tab pill switcher, and pulsing telemetry pills
- `feat(command-bar)`: Redesign query input into full-width hero command bar with spinner & elapsed execution timer
- `feat(presets)`: Add 4 quick preset query chips (`ERR-409-TIMEOUT`, `Tier-1 SLA Targets`, `Zero-Trust Encryption`, `Abstention Guardrail`)
- `feat(toggles)`: Add iOS-style toggle switches for Cross-Encoder Reranker and Live NLI Entailment Judge, plus collapsible ingestion drawer
- `feat(loading)`: Implement pulsing skeleton shimmer loading state to eliminate layout shift during Ollama generation
- `feat(results)`: Implement asymmetric 60/40 2-column workspace with grounded status pill, citations stream, verbatim quotes, and animated NLI evaluation gauge bars
- `feat(retrieval)`: Add chunk inspection cards with rank indicators (`#1`, `#2`, `#3`), dual score visualizer bars (Rerank vs. RRF Fusion), and metadata
- `feat(benchmark)`: Build automated benchmark dashboard with 3 hero KPI bento cards, comparative retrieval matrix table with mini progress bars, and Mode C guardrail card
- `test(build)`: Verify Vite production bundle (`dist/` created in 480ms with 0 errors and 0 warnings)
- `docs(release)`: Update roadmap.md, worklog.md, and gitlog.md for Release v1.3.0

---

## [Release v1.2.0] - Phase 7 Retrieval Differentiation & Singleton Optimization
- `fix(rerank)`: Eliminate redundant sigmoid transformation so CrossEncoder probability is directly preserved (0.0001 for out-of-domain)
- `feat(corpus)`: Split corpus into authoritative primary PDF and distinct decoy catalog Markdown, eliminating duplicate chunks
- `feat(pipeline)`: Implement true Mode A distractor contamination simulation vs Mode B Hybrid Cross-Encoder reranking
- `perf(singleton)`: Implement shared module-level singleton get_shared_cross_encoder() across rag_pipeline and evaluate
- `perf(latency)`: Enforce num_predict=180 and num_ctx=1024 for sub-8s prompt and token generation on CPU
- `test(benchmark)`: Re-run benchmark achieving Mode B Precision@3 of 0.90 (+47.9% gain over Mode A 0.60) and 1.00 Faithfulness
- `test(api)`: Expand backend/test_api.py with benchmark results and full query validation (100% pass)
- `test(frontend)`: Verify Vite production build (596ms, 0 errors)
- `docs(release)`: Update README.md, roadmap.md, fixes.md, worklog.md, and gitlog.md for Release v1.2.0

---

## [Release v1.1.0] - Phase 6 Production Hardening & Full-Stack Expansion
- `feat(corpus)`: Expand sample enterprise corpus in generate_sample_pdf.py to 12 sections with realistic adversarial decoys
- `feat(ingest)`: Update chunk_markdown_by_headers to 550 chars / 100 overlap, indexing 42 granular points with UUID IDs
- `feat(pipeline)`: Differentiate Mode A (dense-only top-3) vs Mode B (hybrid RRF limit=15 to cross-encoder top-3)
- `fix(latency)`: Bound Ollama generation options (num_predict=300, num_ctx=2048, repeat_penalty=1.18, top_k=10, torch_threads=4)
- `feat(eval)`: Implement calibrated Context Precision@3 (T=0.5 scaled entailment + keyword coverage) and sentence-level Faithfulness
- `feat(api)`: Add POST /api/upload for multipart document indexing and GET /api/benchmark for metric distribution
- `feat(frontend)`: Add dual-tab UI in App.jsx (RAG Studio with file upload and Quantitative Benchmark comparison dashboard)
- `feat(launcher)`: Create 1-click cross-platform dev launcher run_dev.py for FastAPI and Vite
- `test(benchmark)`: Re-run automated benchmark suite generating benchmark_results.md and benchmark_results.json
- `docs(release)`: Update README.md, roadmap.md, fixes.md, worklog.md, and gitlog.md for Release v1.1.0

---

## [Release v1.0.0] - Phases 1 to 5 Complete
- `feat(env)`: Initialize directory layout and install dependencies with uv
- `feat(ingest)`: Add reportlab document generator and FastEmbed dual-vector storage in Qdrant
- `feat(pipeline)`: Implement hybrid retrieval (Dense + BM25 RRF), BGE Cross-Encoder reranker, and Ollama Pydantic schema
- `fix(pipeline)`: Add sigmoid logit normalization, defensive JSON stripping, token boundary repair, and 0.55 abstention threshold
- `fix(thermal)`: Offload to CPU, throttle PyTorch threads to 2, and cap generation to 512 tokens to eliminate thermal throttling
- `feat(eval)`: Implement local NLI Cross-Encoder Faithfulness and Precision evaluator
- `feat(api)`: Add FastAPI REST interface with CORS, health check, and /api/ingest endpoint
- `test(api)`: Implement automated TestClient endpoint verification in backend/test_api.py
- `test(benchmark)`: Build automated benchmark suite evaluating Mode A, Mode B, and Mode C guardrails
- `feat(frontend)`: Scaffold React client with query dashboard, metrics cards, and chunk inspector, verifying npm build
- `docs(readme)`: Author comprehensive production README with architecture diagram, tech stack rationale, and benchmark table
- `docs(status)`: Update roadmap.md, worklog.md, fixes.md, and gitlog.md

---

## Commit Message Standard
- `feat(...)`: New functionality or pipeline stage
- `fix(...)`: Bug fix or error resolution
- `perf(...)`: Latency, CPU, or memory optimization
- `docs(...)`: README, benchmark tables, or architectural documentation
- `test(...)`: Verification scripts or benchmark evaluations