#!/usr/bin/env python3
"""Test script for lightweight JSON output."""

import sys
import json
sys.path.insert(0, 'src')

from server import (
    KnowledgeBaseMCPServer,
    make_snippet,
    compact_metadata,
    format_citation
)

def test_helpers():
    """Test helper functions."""
    print("=== Testing Helper Functions ===\n")
    
    # Test make_snippet
    long_text = "This is a very long text. " * 50
    snippet = make_snippet(long_text, 100)
    print(f"✓ make_snippet: {len(snippet)} chars")
    print(f"  Preview: {snippet[:80]}...\n")
    
    # Test compact_metadata
    full_meta = {
        "filename": "test.md",
        "relative_path": "docs/test.md",
        "doc_id": "abc123",
        "h1": "Main Title",
        "h2": "Subsection",
        "chunk_id": 5,
        "total_chunks": 10,
        "start_char": 100,
        "end_char": 500,
        "source": "/full/path/docs/test.md",
        "embedding": [0.1, 0.2, 0.3],  # Should be removed
        "large_field": "x" * 1000,  # Should be removed
    }
    compact = compact_metadata(full_meta)
    print(f"✓ compact_metadata: {len(full_meta)} fields → {len(compact)} fields")
    print(f"  Kept: {sorted(compact.keys())}\n")
    
    # Test format_citation
    citation = format_citation(full_meta)
    print(f"✓ format_citation:")
    print(f"  {citation}\n")


def test_query_json():
    """Test query with JSON output."""
    print("\n=== Testing Query with Lightweight JSON ===\n")
    
    server = KnowledgeBaseMCPServer()
    result = server.ingestion.query("git stash", n_results=2)
    
    print(f"Found {result['count']} results\n")
    
    # Simulate the lightweight JSON construction
    items = []
    for rank, (doc, metadata, distance, doc_id) in enumerate(zip(
        result['results']['documents'][0],
        result['results']['metadatas'][0],
        result['results']['distances'][0],
        result['results']['ids'][0]
    ), 1):
        snippet = make_snippet(doc, 400)
        score = 1 - float(distance)
        citation = format_citation(metadata)
        compact_meta = compact_metadata(metadata)
        
        item = {
            "rank": rank,
            "id": doc_id,
            "score": score,
            "snippet": snippet,
            "citation": citation,
            "metadata": compact_meta,
        }
        items.append(item)
        
        print(f"--- Result {rank} ---")
        print(f"ID: {doc_id}")
        print(f"Score: {score:.2%}")
        print(f"Citation: {citation}")
        print(f"Snippet: {snippet[:120]}...")
        print(f"Metadata fields: {sorted(compact_meta.keys())}")
        print()
    
    # Show JSON size comparison
    lightweight = {"items": items}
    full_text = {"items": [{"text": d} for d in result['results']['documents'][0]]}
    
    light_size = len(json.dumps(lightweight))
    full_size = len(json.dumps(full_text))
    
    print(f"\n=== JSON Size Comparison ===")
    print(f"Lightweight JSON: {light_size:,} bytes")
    print(f"Full text JSON:   {full_size:,} bytes")
    print(f"Reduction: {(1 - light_size/full_size)*100:.1f}%")


if __name__ == "__main__":
    test_helpers()
    test_query_json()
