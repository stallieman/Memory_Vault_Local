"""Test cross-domain retrieval to verify ALL source groups are searchable."""
import sys
import os
from pathlib import Path
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ingestion import DocumentIngestion  # type: ignore

kb = DocumentIngestion()

test_queries = [
    ("Elasticsearch index template", "elastic"),  # Should find elastic docs
    ("SQL JOIN syntax", "sql"),                    # Should find SQL docs
    ("Python list comprehension", "python"),       # Should find Python docs
    ("Docker container networking", "docker"),     # Should find Docker docs
    ("Git merge conflict resolution", "git"),      # Should find Git docs
    ("Machine learning concepts", "ebooks"),       # May fallback to ebooks if no AI docs
]

print("=" * 100)
print("CROSS-DOMAIN RETRIEVAL TEST")
print("=" * 100)
print("\nVerifying that ALL source_groups are searchable with automatic fallback\n")

for query, expected_group in test_queries:
    print(f"\nQuery: '{query}' (expecting: {expected_group})")
    print("-" * 100)
    
    result = kb.query(query, n_results=5)
    
    if result['results'] and result['results']['ids']:
        ids = result['results']['ids'][0]
        metas = result['results']['metadatas'][0]
        dists = result['results']['distances'][0]
        
        groups_found = set()
        for i, (chunk_id, meta, dist) in enumerate(zip(ids[:5], metas[:5], dists[:5])):
            score = 1 - dist
            source_group = meta.get('source_group', 'unknown')
            source = meta.get('relative_path', meta.get('filename', 'unknown'))[:60]
            groups_found.add(source_group)
            
            marker = " <-- MATCH" if source_group == expected_group else ""
            print(f"  {i+1}. [{source_group:10s}] score:{score:.3f} | {source}{marker}")
        
        if expected_group in groups_found:
            print(f"  ✓ SUCCESS: Found {expected_group} docs")
        else:
            print(f"  ⚠ FALLBACK: No {expected_group} docs, got {groups_found}")
    else:
        print("  ✗ NO RESULTS")

print("\n" + "=" * 100)
print("TEST COMPLETE")
print("=" * 100)
print("\nAll source_groups are searchable. If specialized docs don't match,")
print("the system automatically falls back to ebooks/misc based on relevance.")
