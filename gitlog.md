# Git Commit History & Release Log

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

## Commit Message Standard
- `feat(...)`: New functionality or pipeline stage
- `fix(...)`: Bug fix or error resolution
- `refactor(...)`: Code cleanup without behavior change
- `docs(...)`: README, benchmark tables, or architectural documentation
- `test(...)`: Verification scripts or benchmark evaluations