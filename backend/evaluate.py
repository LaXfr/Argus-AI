import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
import re
from pathlib import Path
from typing import Optional, List
import numpy as np
import torch
torch.set_num_threads(4)

from pydantic import BaseModel
from sentence_transformers import CrossEncoder

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

class JudgeMetrics(BaseModel):
    faithfulness_score: float
    context_precision_score: float
    reasoning: str

_eval_model: Optional[CrossEncoder] = None

def get_eval_model() -> CrossEncoder:
    global _eval_model
    if _eval_model is None:
        _eval_model = CrossEncoder("BAAI/bge-reranker-base", device="cpu")
    return _eval_model

def scaled_sigmoid(logit: float, temp: float = 0.5) -> float:
    """Temperature-scaled sigmoid to prevent score compression and provide crisp discrimination."""
    val = float(logit) / max(0.01, float(temp))
    # Clip to avoid overflow
    val = max(-15.0, min(15.0, val))
    return float(1.0 / (1.0 + np.exp(-val)))

STOPWORDS = {
    "what", "is", "the", "for", "and", "are", "which", "how", "during", "using", 
    "with", "from", "that", "this", "these", "those", "when", "where", "who", "whom",
    "does", "did", "will", "would", "can", "could", "should", "shall", "to", "of", "in", 
    "on", "at", "by", "an", "a", "into", "as", "or"
}

def compute_keyword_overlap(query: str, text: str) -> float:
    """Calculates lexical keyword recall between query key terms and chunk text."""
    raw_tokens = re.findall(r'[a-zA-Z0-9_\-]+', query.lower())
    keywords = [t for t in raw_tokens if len(t) >= 3 and t not in STOPWORDS]
    if not keywords:
        return 0.5
    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw in text_lower)
    return min(1.0, float(matches / len(keywords)))

def evaluate_single(
    question: str, 
    answer: str, 
    chunks: list, 
    model: Optional[CrossEncoder] = None
) -> JudgeMetrics:
    if not chunks or not answer.strip():
        return JudgeMetrics(
            faithfulness_score=0.0, 
            context_precision_score=0.0, 
            reasoning="No context chunks or empty answer provided."
        )

    active_model = model or get_eval_model()
    top_chunks = chunks[:3]

    # 1. Context Precision@3: Temperature-scaled entailment + lexical keyword overlap
    q_chunk_pairs = [[question, c.get("text", "")] for c in top_chunks]
    precision_logits = active_model.predict(q_chunk_pairs)
    
    chunk_precisions = []
    for logit, c in zip(precision_logits, top_chunks):
        entailment = scaled_sigmoid(logit, temp=0.5)
        kw_overlap = compute_keyword_overlap(question, c.get("text", ""))
        # Calibrated combination: 65% entailment + 35% keyword overlap
        score = 0.65 * entailment + 0.35 * kw_overlap
        chunk_precisions.append(score)
        
    context_precision = float(np.mean(chunk_precisions)) if chunk_precisions else 0.0

    # 2. Faithfulness: Sentence-level claim verification against retrieved Top-3 context
    combined_context = " ".join([c.get("text", "") for c in top_chunks])
    
    # Split answer into sentences
    raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if len(s.strip()) > 8]
    if not raw_sentences:
        raw_sentences = [answer.strip()]

    claim_pairs = [[combined_context, s] for s in raw_sentences]
    faithfulness_logits = active_model.predict(claim_pairs)
    
    claim_scores = [scaled_sigmoid(l, temp=0.5) for l in faithfulness_logits]
    faithfulness = float(np.mean(claim_scores)) if claim_scores else 0.0

    reasoning = (
        f"Calibrated CPU Cross-Encoder Judge: Context Precision@3 ({context_precision:.2f}) evaluated across "
        f"{len(top_chunks)} chunks using temperature-scaled entailment (T=0.5) + keyword coverage. "
        f"Faithfulness ({faithfulness:.2f}) verified over {len(raw_sentences)} generated claim sentences."
    )

    return JudgeMetrics(
        faithfulness_score=round(float(np.clip(faithfulness, 0.0, 1.0)), 2),
        context_precision_score=round(float(np.clip(context_precision, 0.0, 1.0)), 2),
        reasoning=reasoning
    )