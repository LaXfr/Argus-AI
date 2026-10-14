# Git Commit History & Release Log

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