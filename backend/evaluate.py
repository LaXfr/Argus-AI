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

from rag_pipeline import get_shared_cross_encoder

class JudgeMetrics(BaseModel):
    faithfulness_score: float
    context_precision_score: float
    reasoning: str

def get_eval_model() -> CrossEncoder:
    """Uses the module-level shared CrossEncoder singleton to eliminate duplicate RAM usage."""
    return get_shared_cross_encoder()

STOPWORDS = {
    "what", "is", "the", "for", "and", "are", "which", "how", "during", "using", 
    "with", "from", "that", "this", "these", "those", "when", "where", "who", "whom",
    "does", "did", "will", "would", "can", "could", "should", "shall", "to", "of", "in", 
    "on", "at", "by", "an", "a", "into", "as", "or", "under"
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

    # 1. Context Precision@3: Evaluates retrieval quality differentiating authoritative vs distractor chunks
    q_chunk_pairs = [[question, c.get("text", "")] for c in top_chunks]
    entailment_scores = active_model.predict(q_chunk_pairs)
    
    chunk_precisions = []
    for score, c in zip(entailment_scores, top_chunks):
        raw_prob = float(score)
        kw_overlap = compute_keyword_overlap(question, c.get("text", ""))
        is_decoy = "legacy" in (c.get("source", "") + c.get("chunk_id", "")).lower()
        
        if is_decoy:
            # Distractor / Decoy chunks carry conflicting facts, penalizing ranking precision
            chunk_score = min(0.35, 0.40 * raw_prob + 0.20 * kw_overlap)
        else:
            chunk_score = 0.65 * raw_prob + 0.35 * kw_overlap
        chunk_precisions.append(chunk_score)
        
    context_precision = float(np.mean(chunk_precisions)) if chunk_precisions else 0.0

    # 2. Faithfulness: Sentence-level claim verification against retrieved Top-3 context
    combined_context = " ".join([c.get("text", "") for c in top_chunks])
    
    raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer) if len(s.strip()) > 8]
    if not raw_sentences:
        raw_sentences = [answer.strip()]

    claim_pairs = [[s, combined_context] for s in raw_sentences]
    claim_scores = [float(l) for l in active_model.predict(claim_pairs)]
    faithfulness = float(np.mean(claim_scores)) if claim_scores else 0.0

    reasoning = (
        f"Calibrated CPU Cross-Encoder Judge: Context Precision@3 ({context_precision:.2f}) evaluated across "
        f"{len(top_chunks)} chunks distinguishing authoritative vs distractor documents. "
        f"Faithfulness ({faithfulness:.2f}) verified over {len(raw_sentences)} generated claim sentences."
    )

    return JudgeMetrics(
        faithfulness_score=round(float(np.clip(faithfulness, 0.0, 1.0)), 2),
        context_precision_score=round(float(np.clip(context_precision, 0.0, 1.0)), 2),
        reasoning=reasoning
    )