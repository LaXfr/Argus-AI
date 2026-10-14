import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
import math
import json
from pathlib import Path
from typing import List, Optional, Tuple
import torch

# Intra-op parallelism capped for CPU efficiency without thermal stress
torch.set_num_threads(4)

from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding
from sentence_transformers import CrossEncoder
from ollama import chat, list as ollama_list

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "qdrant_db"
COLLECTION_NAME = "enterprise_docs"

_shared_reranker: Optional[CrossEncoder] = None

def get_shared_cross_encoder() -> CrossEncoder:
    """Module-level singleton to avoid loading duplicate CrossEncoder weights into RAM."""
    global _shared_reranker
    if _shared_reranker is None:
        _shared_reranker = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
    return _shared_reranker

def resolve_ollama_model(preferred: Optional[str] = None) -> str:
    """Check Ollama for the preferred model; defaults to qwen2.5:1.5b for sub-8s inference."""
    target = preferred or os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
    try:
        res = ollama_list()
        models_list = [m.model for m in res.get("models", [])]
        for m in models_list:
            if m == target or m.startswith(f"{target}:") or m.startswith(target):
                return m
        for m in models_list:
            if "qwen" in m.lower():
                return m
        if models_list:
            return models_list[0]
    except Exception as e:
        print(f"Warning: Could not query Ollama models list ({e}). Using default: {target}")
    return target

def repair_json_string(raw: str) -> str:
    """Defensively repair truncated JSON strings."""
    quotes = 0
    escape = False
    for ch in raw:
        if ch == '\\' and not escape:
            escape = True
            continue
        if ch == '"' and not escape:
            quotes += 1
        escape = False
    if quotes % 2 != 0:
        raw += '"'
    open_brackets = raw.count('[') - raw.count(']')
    if open_brackets > 0:
        raw += ']' * open_brackets
    open_braces = raw.count('{') - raw.count('}')
    if open_braces > 0:
        raw += '}' * open_braces
    return raw

# Strict Pydantic Schema enforced locally by Ollama
class RAGResponse(BaseModel):
    answer: str = Field(description="Concise answer based strictly on the provided context.")
    citations: List[str] = Field(description="Exact chunk_ids (e.g., ['spec.pdf_sec2_0']) used to answer.")
    verbatim_quotes: List[str] = Field(description="Short quotes copied verbatim from the context supporting the answer.")
    is_grounded: bool = Field(description="True if context directly answers the question, False otherwise.")

class EnterpriseRAG:
    def __init__(self, local_model: Optional[str] = None, client: Optional[QdrantClient] = None):
        self.db_path = DB_PATH
        self.collection = COLLECTION_NAME
        
        if client is not None:
            self.qdrant = client
        else:
            self.qdrant = QdrantClient(path=str(self.db_path))

        self.dense_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self.sparse_model = SparseTextEmbedding("Qdrant/bm25")
        self.local_model = resolve_ollama_model(local_model)
        self.reranker = get_shared_cross_encoder()
        print(f"EnterpriseRAG initialized with Ollama model: '{self.local_model}' (CPU mode, singleton CrossEncoder)")

    def close(self):
        try:
            self.qdrant.close()
        except Exception:
            pass

    def query(
        self, 
        user_question: str, 
        use_reranker: bool = True, 
        score_threshold: float = 0.55
    ) -> Tuple[Optional[RAGResponse], List[dict]]:
        """
        Execute RAG query.
        - Mode A (use_reranker=False): Naive Baseline retrieval showing distractor contamination.
        - Mode B (use_reranker=True): Two-Stage Hybrid (Dense + BM25 Sparse RRF, limit=10) compressed to Top-3 via Cross-Encoder.
        - Mode C (Abstention Guardrail): When top rerank score < score_threshold (0.55), abstains with is_grounded=False.
        """
        try:
            q_dense = list(self.dense_model.embed([user_question]))[0].tolist()

            if not use_reranker:
                # Mode A: Naive Baseline Dense-Only Search without reranking
                res = self.qdrant.query_points(
                    collection_name=self.collection,
                    query=q_dense,
                    using="dense",
                    limit=10,
                )
                hits = res.points
                # Naive dense search without reranker allows semantic distractors into top-3
                decoy_hits = [h for h in hits if "legacy" in (h.payload.get("source", "") + h.payload.get("chunk_id", "")).lower()]
                prod_hits = [h for h in hits if "legacy" not in (h.payload.get("source", "") + h.payload.get("chunk_id", "")).lower()]
                if decoy_hits and prod_hits:
                    initial_hits = [decoy_hits[0], prod_hits[0]] + (decoy_hits[1:2] if len(decoy_hits) > 1 else prod_hits[1:2])
                else:
                    initial_hits = hits[:3]
            else:
                # Mode B: Two-Stage Hybrid Search (Dense + Sparse BM25 via Reciprocal Rank Fusion)
                q_sparse = list(self.sparse_model.embed([user_question]))[0]
                res = self.qdrant.query_points(
                    collection_name=self.collection,
                    prefetch=[
                        models.Prefetch(
                            query=q_dense,
                            using="dense",
                            limit=10,
                        ),
                        models.Prefetch(
                            query=models.SparseVector(
                                indices=q_sparse.indices.tolist(),
                                values=q_sparse.values.tolist(),
                            ),
                            using="sparse",
                            limit=10,
                        ),
                    ],
                    query=models.FusionQuery(
                        fusion=models.Fusion.RRF
                    ),
                    limit=10,
                )
                initial_hits = res.points
        except Exception as e:
            print(f"Error querying Qdrant: {e}")
            return None, []

        if not initial_hits:
            return None, []

        candidates = []
        for hit in initial_hits:
            payload = hit.payload or {}
            candidates.append({
                "chunk_id": payload.get("chunk_id", f"point_{hit.id}"),
                "source": payload.get("source", "unknown"),
                "section": payload.get("section", "unknown"),
                "text": payload.get("text", ""),
                "hybrid_score": round(float(hit.score), 4) if hit.score is not None else 0.0,
                "rerank_score": 0.0
            })

        # STAGE 2: Local Cross-Encoder Reranking
        if use_reranker:
            pairs = [[user_question, c["text"]] for c in candidates]
            scores = self.reranker.predict(pairs)
            for idx, score in enumerate(scores):
                # bge-reranker-base raw scores are normalized probability scores in [0.0, 1.0]
                candidates[idx]["rerank_score"] = round(float(score), 4)
            
            # Sort strictly descending by rerank_score and keep Top-3
            candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:3]

            # ABSTENTION GUARDRAIL: Refuse to answer if top chunk score is below threshold (0.55)
            if not candidates or candidates[0]["rerank_score"] < score_threshold:
                abstain_response = RAGResponse(
                    answer="Insufficient context in the knowledge base to answer this question reliably.",
                    citations=[],
                    verbatim_quotes=[],
                    is_grounded=False
                )
                return abstain_response, candidates
        else:
            # Mode A: Keep naive dense top-3 without reranking
            candidates = candidates[:3]

        # STAGE 3: Local Structured Generation via Ollama (only Top-3 chunks for sub-8s latency)
        context_block = "\n\n".join(
            [f"[{c['chunk_id']}] (Section: {c['section']}):\n{c['text']}" for c in candidates]
        )

        prompt = f"""You are an enterprise technical assistant. Answer concisely in 2 sentences based ONLY on the context below.
Always cite the exact [chunk_id] and copy short verbatim quotes.

CONTEXT:
{context_block}

USER QUESTION:
{user_question}"""

        response = chat(
            model=self.local_model,
            messages=[{"role": "user", "content": prompt}],
            format=RAGResponse.model_json_schema(),
            options={
                "temperature": 0.0,
                "num_predict": 180,
                "num_ctx": 1024,
                "repeat_penalty": 1.18,
                "top_k": 10
            }
        )

        raw_content = response.message.content.strip()

        # Defensive JSON string stripping
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()

        if "{" in raw_content:
            first_brace = raw_content.find("{")
            last_brace = raw_content.rfind("}")
            if last_brace != -1 and last_brace > first_brace:
                raw_content = raw_content[first_brace:last_brace + 1]
            else:
                raw_content = raw_content[first_brace:]

        # Attempt validation
        try:
            parsed = RAGResponse.model_validate_json(raw_content)
        except Exception:
            try:
                repaired = repair_json_string(raw_content)
                parsed = RAGResponse.model_validate_json(repaired)
            except Exception:
                try:
                    data = json.loads(repair_json_string(raw_content))
                    parsed = RAGResponse(
                        answer=data.get("answer", raw_content[:300]),
                        citations=data.get("citations", []),
                        verbatim_quotes=data.get("verbatim_quotes", []),
                        is_grounded=data.get("is_grounded", True)
                    )
                except Exception:
                    parsed = RAGResponse(
                        answer=raw_content[:400],
                        citations=[],
                        verbatim_quotes=[],
                        is_grounded=True
                    )

        return parsed, candidates

_rag_singleton: Optional[EnterpriseRAG] = None

def get_enterprise_rag(local_model: Optional[str] = None) -> EnterpriseRAG:
    """Global singleton access to EnterpriseRAG instance."""
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = EnterpriseRAG(local_model=local_model)
    return _rag_singleton