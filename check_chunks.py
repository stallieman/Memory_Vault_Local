"""Check what chunks exist for the index template documentation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ingestion import DocumentIngestion  # type: ignore

kb = DocumentIngestion()

# Search with a specific query about index templates
query = "PUT _index_template example settings mappings"
results = kb.query(query, n_results=20)

print(f"\nTop 20 results for query: '{query}'\n")
print("=" * 100)

if results['results'] and results['results']['ids']:
    ids = results['results']['ids'][0]
    docs = results['results']['documents'][0]
    metas = results['results']['metadatas'][0]
    dists = results['results']['distances'][0]
    
    for i, (chunk_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists)):
        score = 1 - dist
        print(f"\nRank {i+1}: {chunk_id} (score: {score:.3f})")
        print(f"  File: {meta.get('relative_path', 'N/A')}")
        print(f"  Length: {len(doc)} chars")
        print(f"  Preview: {doc[:200].replace(chr(10), ' ')}...")
        print()
else:
    print("No results found")
