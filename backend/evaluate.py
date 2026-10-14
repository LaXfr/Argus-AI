import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
from pathlib import Path
from typing import Optional
import numpy as np
import torch
torch.set_num_threads(2)

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

def sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))

def evaluate_single(question: str, answer: str, chunks: list, model: Optional[CrossEncoder] = None) -> JudgeMetrics:
    if not chunks:
        return JudgeMetrics(
            faithfulness_score=0.0, 
            context_precision_score=0.0, 
            reasoning="No chunks retrieved."
        )

    active_model = model or get_eval_model()

    # 1. Context Precision: How relevant are the top-3 chunks to the user's question?
    top_chunks = chunks[:3]
    q_chunk_pairs = [[question, c.get("text", "")] for c in top_chunks]
    precision_logits = active_model.predict(q_chunk_pairs)
    context_precision = float(np.mean([sigmoid(score) for score in precision_logits]))

    # 2. Faithfulness (Hallucination Check): Is the generated answer supported by the top chunks?
    combined_context = " ".join([c.get("text", "") for c in top_chunks])
    faithfulness_logit = active_model.predict([[combined_context, answer]])[0]
    faithfulness = sigmoid(faithfulness_logit)

    reasoning = (
        f"Evaluated locally via CPU Cross-Encoder entailment across top-{min(3, len(chunks))} chunks "
        f"(Zero GPU load & zero external API calls)."
    )

    return JudgeMetrics(
        faithfulness_score=round(faithfulness, 2),
        context_precision_score=round(context_precision, 2),
        reasoning=reasoning
    )