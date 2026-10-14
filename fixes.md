# Issue Tracker & Resolution Log

## Known Pitfalls & Solutions

### 1. Qdrant Local Storage Lock (`qdrant_db`)
- **Issue:** Attempting to run `ingest.py` while FastAPI is actively running can trigger a SQLite/storage lock error because embedded Qdrant allows single-process access to the local directory.
- **Fix:** Provide shared singleton client access in `backend/api.py` via `/api/ingest`, or ensure ingestion scripts close handles (`rag.close()`) before other processes initialize.

### 2. Ollama JSON Output Parsing & Defensive Stripping
- **Issue:** Smaller local models (like `qwen2.5:1.5b` or `llama3.2:3b`) may occasionally prepend markdown code blocks (````json ... ````) or conversational preambles despite `format=RAGResponse.model_json_schema()`.
- **Fix:** Strip leading/trailing markdown triple-backticks and slice string between first `{` and last `}` before calling `RAGResponse.model_validate_json(raw_text)`. Implemented `repair_json_string()` to close unclosed quotes/braces if tokens truncate.

### 3. Cross-Encoder Logit Scaling
- **Issue:** Raw Cross-Encoder reranker outputs are unbounded logits (can be negative, e.g., `-3.4` or `+4.1`), confusing UI percentage displays and thresholding.
- **Fix:** Apply a sigmoid function $\frac{1}{1 + e^{-x}}$ to map reranker scores to a clean `[0.0, 1.0]` probability range.

### 4. Vite Frontend Build Entrypoints
- **Issue:** Missing `frontend/package.json` (0 bytes) and Vite HTML/JS entrypoints (`index.html`, `main.jsx`, `vite.config.js`) prevented `npm run build`.
- **Fix:** Configured standard Vite React configuration with dependencies (`react`, `react-dom`, `@vitejs/plugin-react`), created root HTML template, and verified build (`npm run build` completed in 633ms).

### 5. FastEmbed Integration in Qdrant-Client 1.19.1
- **Issue:** `qdrant-client` 1.19.1 deprecated helper methods `client.set_model()` and `client.add()`. Calling them raised `AttributeError: 'QdrantClient' object has no attribute 'set_model'`.
- **Fix:** Integrated `fastembed.TextEmbedding` and `fastembed.SparseTextEmbedding` directly with Qdrant's native `create_collection(vectors_config=..., sparse_vectors_config=...)` and `query_points(prefetch=[...], query=FusionQuery(fusion=Fusion.RRF))`.

### 6. Ollama Infinite Generation Loop & GPU Thermal Throttling
- **Issue:** Running Ollama on GPU caused severe thermal throttling (GPU temperature reached 90°C and triggered "GPU is lost"). Furthermore, without a hard token limit (`num_predict`), Ollama entered an infinite repetition loop generating 22,000+ tokens for 33+ minutes.
- **Fix:**
  1. Offloaded Ollama and SentenceTransformers to CPU using `CUDA_VISIBLE_DEVICES=""`.
  2. Capped PyTorch intra-op threads with `torch.set_num_threads(2)`.
  3. Set a strict generation ceiling in Ollama options: `options={"temperature": 0.0, "num_predict": 512}`.
  4. Reduced per-query inference from 33 minutes to ~15-20 seconds with 0% GPU load.

### 7. Abstention Guardrail Threshold Calibration
- **Issue:** When using sigmoid normalization, `sigmoid(0.0) = 0.5000`. An out-of-domain query with 0.0 correlation scored `0.5000`. A threshold of `0.35` allowed the query through (`0.5000 >= 0.35`) instead of abstaining.
- **Fix:** Calibrated `score_threshold` to `0.55` (aligning with probability theory where $>0.50$ represents positive entailment). Out-of-domain queries ($score = 0.5000$) now reliably abstain (`is_grounded=False`) with zero hallucination.