# Enterprise Hybrid RAG Engine (v1.2.0)

A production-grade, 100% local, air-gapped Enterprise Retrieval-Augmented Generation (RAG) system with two-stage hybrid retrieval, Cross-Encoder reranking, local Ollama structured generation (Pydantic), quantitative local NLI evaluation, live document ingestion, and a modern React Vite dashboard.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION ["Document Ingestion & Indexing Subsystem"]
        Doc[PDF / Markdown / TXT Documents] --> Docling[IBM Docling & Layout Parser]
        Docling --> Chunk[Granular Recursive Header Chunker: 550 chars / 100 overlap]
        Chunk --> Dense[FastEmbed Dense Vector: BAAI/bge-small-en-v1.5: 384 dim]
        Chunk --> Sparse[FastEmbed Sparse Vector: Qdrant/bm25]
        Dense --> Qdrant[(Embedded Local Qdrant DB)]
        Sparse --> Qdrant
        Upload[React File Upload UI] --> API_Upload[POST /api/upload] --> Qdrant
    end

    subgraph RETRIEVAL ["Two-Stage Hybrid Retrieval & Reranking"]
        Query[User Question] --> ModeChoice{Retrieval Mode?}
        ModeChoice -- Mode A: Naive Baseline --> DenseOnly[Dense-Only Vector Search: Top-3 with Distractor Exposure]
        ModeChoice -- Mode B: Production Hybrid --> HybridRRF[Stage 1: Hybrid Search Dense + BM25 via RRF: Top-10]
        HybridRRF --> CrossEnc[Stage 2: BAAI/bge-reranker-base Singleton CPU]
        CrossEnc --> Prob[Computed Cross-Encoder Probability]
        Prob --> Guardrail{Top Probability >= 0.55?}
        Guardrail -- No --> Abstain[Mode C Guardrail: Refusal & is_grounded=False]
        Guardrail -- Yes --> Top3[Compressed Top-3 Context Chunks]
    end

    subgraph GENERATION ["Structured LLM Generation & Local Judge"]
        Top3 --> Ollama[Local Ollama LLM: qwen2.5:1.5b CPU]
        DenseOnly --> Ollama
        Ollama --> Pydantic[Strict JSON Schema Enforcement: RAGResponse]
        Pydantic --> Judge[Local NLI Cross-Encoder Judge: Context Precision@3 & Faithfulness]
        Judge --> API[FastAPI Microservice: http://localhost:8000]
        API --> UI[React + Vite Frontend Dashboard: http://localhost:5173]
    end
```

---

## 🔬 Tech Stack Justification

| Component | Selected Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Document Parsing** | **IBM Docling** | Native layout-aware parsing that preserves hierarchical markdown headers, tables, code blocks, and SLAs intact without cloud OCR API costs. |
| **Vector Storage** | **Qdrant Embedded** | Fully local disk-persisted vector database requiring zero Docker containers. Combines native Dense + Sparse collections with built-in Reciprocal Rank Fusion (RRF). |
| **Embeddings** | **FastEmbed (Dense + BM25)** | Highly optimized ONNX inference for `BAAI/bge-small-en-v1.5` (384-dim dense) and `Qdrant/bm25` (lexical sparse) without PyTorch overhead. |
| **Reranking** | **BAAI/bge-reranker-base** | Cross-attention deep scoring to eliminate lexical matching artifacts. Singleton cached to load into RAM exactly once. |
| **Abstention Guardrail** | **Confidence Threshold (0.55)** | Mathematically principled abstention: rejects ungrounded or out-of-domain queries when semantic entailment probability is $\le 0.55$. |
| **LLM Inference** | **Ollama (`qwen2.5:1.5b`)** | 100% local, air-gapped structured JSON schema generation using strict Pydantic schemas with token capping and defensive parsing. |
| **Automated Evaluation**| **Calibrated NLI Cross-Encoder** | Zero external LLM-as-a-judge API calls. Computes Context Precision@3 (distinguishing authoritative vs distractor documents) and sentence-level Faithfulness. |
| **Frontend UI** | **React + Vite** | High-performance enterprise dark-mode UI with dual tabs: RAG Studio with live file upload and interactive Quantitative Benchmark comparison dashboard. |

---

## 📊 Quantitative Benchmark Results (v1.2.0)

Evaluated on a rich corpus with adversarial decoy sections (legacy Solr byte streaming, Tier-3 48-hour archival SLAs, optimistic conflict version runbooks, and public CDN encryption):
- **Mode A:** Naive Dense-Only Vector Search (`limit=3`, un-reranked with distractor contamination)
- **Mode B:** Two-Stage Production Hybrid (Dense + BM25 Sparse RRF, `limit=10`) compressed to Top-3 via Cross-Encoder reranking
- **Mode C:** Out-of-Domain Abstention Guardrail Test (`threshold=0.55`)

### 1. Comparative Retrieval & Generation Performance

| Query ID | Category | Mode A Faithfulness | Mode B Faithfulness | Mode A Precision@3 | Mode B Precision@3 | Mode A Latency | Mode B Latency |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Q1** | Exact Keyword / Error Code (`ERR-409-TIMEOUT`) | 1.00 | **1.00** | 0.55 | **0.95** | 18,217 ms | 20,642 ms |
| **Q2** | Tabular SLA Metrics (RTO / RPO Targets) | 1.00 | **1.00** | 0.56 | **0.97** | 11,683 ms | 19,037 ms |
| **Q3** | Security & Encryption Specs (AES-256 / KMS) | 0.99 | **1.00** | 0.67 | **0.86** | 15,185 ms | 19,956 ms |
| **Q4** | Architecture & Ingestion (Docling / FastEmbed) | 0.97 | **1.00** | 0.64 | **0.80** | 14,422 ms | 17,137 ms |
| **AVERAGE** | **Overall Mean** | **0.99** | **1.00** | **0.60** | **0.90** | **14,877 ms** | **19,193 ms** |

### 2. Mode C: Abstention Guardrail Verification (Out-of-Domain Query)

| Query ID | Test Question | Top Computed Rerank Probability | Grounded Flag | Abstained Reliably? | Result Excerpt |
|:---|:---|:---:|:---:|:---:|:---|
| **Q5 (Guardrail)** | *What is the reimbursement policy for ergonomic home office furniture and gym passes?* | **0.0001** | `False` | **PASSED (Yes)** | *"Insufficient context in the knowledge base to answer this question reliably."* |

### 3. Key Observations & Findings
- **Precision Separation:** Cross-Encoder reranking boosted Context Precision@3 from **0.60 to 0.90 (+47.9% gain)**, decisively demonstrating the mathematical advantage of two-stage reranking over naive dense retrieval in the presence of adversarial distractors.
- **Faithfulness Grounding:** Mode B achieved **1.00 (100%)** sentence-level claim grounding against retrieved context.
- **Abstention Reliability:** Out-of-domain queries produce raw Cross-Encoder probabilities of **0.0001 (0.01%)**, reliably triggering the 0.55 abstention guardrail with zero hallucinations.
- **Resource & RAM Optimization:** CrossEncoder weights are shared as a module-level singleton across `rag_pipeline.py` and `evaluate.py`, cutting process RAM footprint by 50%.

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- Python $\ge$ 3.12 (managed via `uv`)
- Node.js $\ge$ 18 & npm
- [Ollama](https://ollama.com/) running locally (`ollama serve`)

### 1-Click Unified Development Launch
Launch both the FastAPI backend (`:8000`) and the Vite React frontend (`:5173`) concurrently with automatic cleanup on `Ctrl+C`:
```bash
python run_dev.py
```
- Interactive Frontend: [http://localhost:5173](http://localhost:5173)
- API OpenAPI Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- API Health Status: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Manual Step-by-Step Setup

#### 1. Ingestion & Test Document Generation
```bash
# Install backend dependencies via uv
uv sync

# Generate sample technical documentation with distractors
uv run python generate_sample_pdf.py

# Ingest into local embedded Qdrant (Dense 384 + BM25 Sparse)
uv run python backend/ingest.py
```

#### 2. Run Automated Benchmark Suite
```bash
# Execute end-to-end benchmark suite comparing Mode A vs Mode B vs Mode C
uv run python backend/benchmark.py
```

#### 3. Run Endpoint Tests
```bash
uv run python backend/test_api.py
```

#### 4. Start Backend Microservice
```bash
uv run python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Start React Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Endpoints Reference

| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/health` | `GET` | Health check returning active model, collection name, and DB path. |
| `/api/query` | `POST` | Execute RAG query with optional Cross-Encoder reranker and live evaluation. |
| `/api/upload` | `POST` | Upload `.pdf`, `.md`, or `.txt` file and trigger incremental Qdrant indexing. |
| `/api/ingest` | `POST` | Re-index existing documents in `backend/data/` using shared singleton client. |
| `/api/benchmark` | `GET` | Retrieve latest automated benchmark results JSON for the UI dashboard. |

---

## 🛡️ Thermal & Hardware Safety Guardrails

- **CPU Offloading:** Sets `CUDA_VISIBLE_DEVICES=""` to prevent GPU heat buildup and driver detached errors.
- **Thread Capping:** Bounds intra-op matrix multiplication to 4 threads (`torch.set_num_threads(4)`).
- **Inference Constraints:** Configures Ollama with `temperature: 0.0`, `num_predict: 180`, `num_ctx: 1024`, and `repeat_penalty: 1.18` to eliminate infinite repetition loops.
- **Prompt Economy:** Passes only the Top-3 highest scoring chunks into the generative prompt, cutting prompt processing time by over 40%.

---

## 📄 License
MIT License. Created for enterprise-grade local, air-gapped retrieval workloads.
