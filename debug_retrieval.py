"""Debug retrieval to see why only 3 chunks are returned."""
import sys
import os
from pathlib import Path
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ingestion import DocumentIngestion  # type: ignore
from local_rag_ollama import RAG_TOP_K, RAG_FILTER_TOC, RAG_MAX_PER_SOURCE, RAG_MIN_SCORE  # type: ignore

question = "create an index template for a dummy index, with dummy settings and mapping with different types"

print("=" * 80)
print("DEBUGGING RETRIEVAL")
print("=" * 80)
print(f"RAG_TOP_K: {RAG_TOP_K}")
print(f"RAG_FILTER_TOC: {RAG_FILTER_TOC}")
print(f"RAG_MAX_PER_SOURCE: {RAG_MAX_PER_SOURCE}")
print(f"RAG_MIN_SCORE: {RAG_MIN_SCORE}")
print()

kb = DocumentIngestion()

# Do a direct query
fetch_count = RAG_TOP_K * 3 if RAG_FILTER_TOC else RAG_TOP_K
print(f"Fetching {fetch_count} initial candidates...")
result = kb.query(question, n_results=fetch_count)

ids = result["results"]["ids"][0]
docs = result["results"]["documents"][0]
metas = result["results"]["metadatas"][0]
dists = result["results"]["distances"][0]

print(f"Retrieved {len(ids)} candidates\n")

for i, (chunk_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists)):
    score = 1 - dist
    source = meta.get("relative_path", "unknown")
    
    # Check filtering
    passes_score = score >= RAG_MIN_SCORE
    status = "PASS" if passes_score else f"FILTERED (score {score:.3f} < {RAG_MIN_SCORE})"
    
    print(f"{i+1:2d}. {chunk_id} | score:{score:.3f} | {status}")
    print(f"    Source: {source[:70]}")
    print()
