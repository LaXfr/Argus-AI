import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
import math
import json
from pathlib import Path
from typing import List, Optional, Tuple
import torch
# Throttle threads to prevent CPU overheating
torch.set_num_threads(2)

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

def sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + math.exp(-float(x))))

def resolve_ollama_model(preferred: str = "qwen2.5:3b") -> str:
    """Check Ollama for the preferred model; fallback gracefully if not present."""
    try:
        res = ollama_list()
        models_list = [m.model for m in res.get("models", [])]
        for m in models_list:
            if m == preferred or m.startswith(f"{preferred}:") or m.startswith(preferred):
                return m
        for m in models_list:
            if "qwen" in m.lower():
                return m
        if models_list:
            return models_list[0]
    except Exception as e:
        print(f"Warning: Could not query Ollama models list ({e}). Using default: {preferred}")
    return preferred

def repair_json_string(raw: str) -> str:
    """Repair truncated JSON if tokens cut off."""
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

# 1. Strict Pydantic Schema enforced locally by Ollama
class RAGResponse(BaseModel):
    answer: str = Field(description="Comprehensive answer based strictly on the provided context.")
    citations: List[str] = Field(description="Exact chunk_ids (e.g., ['report.pdf_sec2_0']) used to answer.")
    verbatim_quotes: List[str] = Field(description="Exact short quotes copied from the context supporting the answer.")
    is_grounded: bool = Field(description="True if the context directly answers the question, False otherwise.")

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
        self.local_model = resolve_ollama_model(local_model or "qwen2.5:3b")
        print(f"EnterpriseRAG initialized with Ollama model: '{self.local_model}' (CPU mode)")
        
        # Local Cross-Encoder Reranker explicitly forced to CPU with thermal throttling protection
        self.reranker = CrossEncoder("BAAI/bge-reranker-base", device="cpu")

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
        limit = 15 if use_reranker else 5
        
        # STAGE 1: Local Hybrid Retrieval (Dense + BM25 Sparse fused via RRF)
        try:
            q_dense = list(self.dense_model.embed([user_question]))[0].tolist()
            q_sparse = list(self.sparse_model.embed([user_question]))[0]

            res = self.qdrant.query_points(
                collection_name=self.collection,
                prefetch=[
                    models.Prefetch(
                        query=q_dense,
                        using="dense",
                        limit=limit,
                    ),
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=q_sparse.indices.tolist(),
                            values=q_sparse.values.tolist(),
                        ),
                        using="sparse",
                        limit=limit,
                    ),
                ],
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF
                ),
                limit=limit,
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
                candidates[idx]["rerank_score"] = round(sigmoid(float(score)), 4)
            
            candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:5]

            # ABSTENTION GUARDRAIL: Refuse to answer if top chunk score is below normalized threshold (0.55)
            if not candidates or candidates[0]["rerank_score"] < score_threshold:
                abstain_response = RAGResponse(
                    answer="Insufficient context in the knowledge base to answer this question reliably.",
                    citations=[],
                    verbatim_quotes=[],
                    is_grounded=False
                )
                return abstain_response, candidates
        else:
            candidates = candidates[:5]

        # STAGE 3: Local Structured Generation via Ollama
        context_block = "\n\n".join(
            [f"[{c['chunk_id']}] (Section: {c['section']}):\n{c['text']}" for c in candidates]
        )

        prompt = f"""You are an enterprise retrieval assistant. Answer the user's question concisely ONLY using the context below.
Always cite the exact [chunk_id] and copy verbatim supporting quotes. Return strictly valid JSON adhering to the required schema.

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
                "num_predict": 512,
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