# Git Commit History & Release Log

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
- `refactor(...)`: Code cleanup without behavior change
- `docs(...)`: README, benchmark tables, or architectural documentation
- `test(...)`: Verification scripts or benchmark evaluations