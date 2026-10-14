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

def chunk_markdown_by_headers(md_text: str, source_name: str, max_chars: int = 550, overlap: int = 100):
    """Splits Markdown by headings so tables and sections stay intact, then sub-chunks with overlap."""
    import re
    # Match markdown headers (#, ##, ###)
    raw_sections = re.split(r'\n(?=#{1,4}\s+)', md_text)
    chunks, metadata = [], []
    step = max(100, max_chars - overlap)
    
    for i, sec in enumerate(raw_sections):
        clean_sec = sec.strip()
        if not clean_sec:
            continue
        header_line = clean_sec.split("\n")[0].replace("#", "").strip()[:80]
        
        if len(clean_sec) <= max_chars:
            chunks.append(clean_sec)
            metadata.append({
                "source": source_name,
                "section": header_line,
                "chunk_id": f"{source_name}_sec{i}_0"
            })
        else:
            for start in range(0, len(clean_sec), step):
                chunk_text = clean_sec[start : start + max_chars].strip()
                if len(chunk_text) < 40 and start > 0:
                    continue  # skip tiny trailing fragments
                chunks.append(chunk_text)
                metadata.append({
                    "source": source_name,
                    "section": header_line,
                    "chunk_id": f"{source_name}_sec{i}_{start}"
                })
    return chunks, metadata

def ingest_pdfs(data_dir: Optional[Path | str] = None, client: Optional[QdrantClient] = None, recreate: bool = False) -> int:
    import uuid
    target_data_dir = Path(data_dir) if data_dir else DATA_DIR
    target_data_dir.mkdir(parents=True, exist_ok=True)
    
    converter = DocumentConverter()
    all_chunks, all_meta = [], []

    files = sorted(list(target_data_dir.glob("*.pdf")) + list(target_data_dir.glob("*.md")) + list(target_data_dir.glob("*.txt")))
    
    for doc_path in files:
        print(f"Parsing {doc_path.name}...")
        if doc_path.suffix.lower() in [".md", ".txt"]:
            with open(doc_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        else:
            result = converter.convert(str(doc_path))
            md_text = result.document.export_to_markdown()
        
        chunks, meta = chunk_markdown_by_headers(md_text, doc_path.name, max_chars=550, overlap=100)
        all_chunks.extend(chunks)
        all_meta.extend(meta)

    if not all_chunks:
        print(f"No documents (.pdf, .md, .txt) found in {target_data_dir}!")
        return 0

    print(f"Extracting vectors for {len(all_chunks)} chunks (BAAI/bge-small-en-v1.5 Dense + Qdrant/bm25 Sparse)...")
    dense_model = get_dense_model()
    sparse_model = get_sparse_model()

    dense_embeddings = list(dense_model.embed(all_chunks))
    sparse_embeddings = list(sparse_model.embed(all_chunks))

    active_client = client or get_qdrant_client()
    
    if recreate:
        try:
            active_client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection '{COLLECTION_NAME}' for clean re-indexing.")
        except Exception:
            pass
            
    ensure_collection(active_client, COLLECTION_NAME)

    points = []
    for idx, (chunk_text, meta, d_emb, s_emb) in enumerate(zip(all_chunks, all_meta, dense_embeddings, sparse_embeddings)):
        # Deterministic UUID based on source, section, and text slice
        point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{meta.get('source')}_{meta.get('chunk_id')}_{chunk_text[:40]}"))
        point = models.PointStruct(
            id=point_uuid,
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
    ingest_pdfs(recreate=True)