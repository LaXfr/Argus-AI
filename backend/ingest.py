import os
import sys
from pathlib import Path
from typing import Optional
from docling.document_converter import DocumentConverter
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "qdrant_db"
COLLECTION_NAME = "enterprise_docs"

_dense_model = None
_sparse_model = None

def get_dense_model() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        _dense_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _dense_model

def get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding("Qdrant/bm25")
    return _sparse_model

def get_qdrant_client(db_path: Optional[Path] = None) -> QdrantClient:
    target_path = str(db_path or DB_PATH)
    return QdrantClient(path=target_path)

def ensure_collection(client: QdrantClient, collection_name: str = COLLECTION_NAME):
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        print(f"Creating Qdrant hybrid collection '{collection_name}' (Dense 384 + BM25 Sparse)...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams()
            }
        )
    else:
        print(f"Collection '{collection_name}' already exists.")

def chunk_markdown_by_headers(md_text: str, source_name: str, max_chars: int = 1500):
    """Splits Markdown by headings so tables and sections stay intact."""
    sections = md_text.split("\n## ")
    chunks, metadata = [], []
    
    for i, sec in enumerate(sections):
        clean_sec = sec.strip()
        if not clean_sec:
            continue
        # Add header prefix back if split removed it
        if i > 0:
            clean_sec = "## " + clean_sec
        
        # Further split if a section is longer than max_chars
        for start in range(0, len(clean_sec), max_chars - 150):
            chunk_text = clean_sec[start : start + max_chars]
            header_line = clean_sec.split("\n")[0].replace("#", "").strip()[:80]
            chunks.append(chunk_text)
            metadata.append({
                "source": source_name,
                "section": header_line,
                "chunk_id": f"{source_name}_sec{i}_{start}"
            })
    return chunks, metadata

def ingest_pdfs(data_dir: Optional[Path | str] = None, client: Optional[QdrantClient] = None) -> int:
    target_data_dir = Path(data_dir) if data_dir else DATA_DIR
    target_data_dir.mkdir(parents=True, exist_ok=True)
    
    converter = DocumentConverter()
    all_chunks, all_meta = [], []

    files = list(target_data_dir.glob("*.pdf")) + list(target_data_dir.glob("*.md"))
    
    for doc_path in files:
        print(f"Parsing {doc_path.name}...")
        if doc_path.suffix.lower() == ".md":
            with open(doc_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        else:
            result = converter.convert(str(doc_path))
            md_text = result.document.export_to_markdown()
        
        chunks, meta = chunk_markdown_by_headers(md_text, doc_path.name)
        all_chunks.extend(chunks)
        all_meta.extend(meta)

    if not all_chunks:
        print(f"No documents (.pdf or .md) found in {target_data_dir}!")
        return 0

    print(f"Extracting vectors for {len(all_chunks)} chunks (BAAI/bge-small-en-v1.5 Dense + Qdrant/bm25 Sparse)...")
    dense_model = get_dense_model()
    sparse_model = get_sparse_model()

    dense_embeddings = list(dense_model.embed(all_chunks))
    sparse_embeddings = list(sparse_model.embed(all_chunks))

    active_client = client or get_qdrant_client()
    ensure_collection(active_client, COLLECTION_NAME)

    points = []
    for idx, (chunk_text, meta, d_emb, s_emb) in enumerate(zip(all_chunks, all_meta, dense_embeddings, sparse_embeddings)):
        point = models.PointStruct(
            id=idx + 1,
            vector={
                "dense": d_emb.tolist(),
                "sparse": models.SparseVector(
                    indices=s_emb.indices.tolist(),
                    values=s_emb.values.tolist()
                )
            },
            payload={
                "text": chunk_text,
                "chunk_id": meta.get("chunk_id", f"chunk_{idx}"),
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", "unknown"),
            }
        )
        points.append(point)

    print(f"Upserting {len(points)} hybrid points into Qdrant collection '{COLLECTION_NAME}'...")
    active_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )
    print(f"Ingestion Complete! Successfully indexed {len(points)} chunks.")
    return len(points)

if __name__ == "__main__":
    ingest_pdfs()