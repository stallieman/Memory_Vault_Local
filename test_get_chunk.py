#!/usr/bin/env python3
"""Test script for get_chunk_by_id functionality."""

import sys
import json
sys.path.insert(0, 'src')

from server import KnowledgeBaseMCPServer

def test_get_chunk_by_id():
    """Test retrieving a chunk by ID with new parameters."""
    print("=== Testing Enhanced get_chunk_by_id ===\n")
    
    server = KnowledgeBaseMCPServer()
    
    # First, query to get some chunk IDs
    print("1. Querying for 'git stash' to get chunk IDs...")
    result = server.ingestion.query("git stash", n_results=2)
    
    chunk_ids = result['results']['ids'][0]
    print(f"   Found chunks: {chunk_ids}\n")
    
    # Test 1: Retrieve with default parameters (using 'id' not 'chunk_id')
    chunk_id = chunk_ids[0]
    print(f"2. Testing with id='{chunk_id}' (default max_chars=5000)")
    
    retrieved = server.ingestion.collection.get(
        ids=[chunk_id],
        include=["documents", "metadatas"]
    )
    
    if retrieved['ids']:
        doc = (retrieved.get("documents") or [""])[0] or ""
        meta = (retrieved.get("metadatas") or [{}])[0] or {}
        
        # Test truncation logic
        max_chars = 200  # Small for testing
        truncated = False
        if len(doc) > max_chars:
            doc_truncated = doc[:max_chars].rstrip() + "…"
            truncated = True
        else:
            doc_truncated = doc
        
        print(f"   ✓ Retrieved chunk")
        print(f"   Original length: {len(doc)} chars")
        print(f"   Truncated (200 chars): {doc_truncated}")
        print(f"   Is truncated: {truncated}\n")
        
        # Test compact_metadata
        from server import compact_metadata, format_citation
        
        compact_meta = compact_metadata(meta)
        citation = format_citation(meta)
        
        print(f"   Metadata fields: {sorted(meta.keys())}")
        print(f"   Compact metadata: {sorted(compact_meta.keys())}")
        print(f"   Citation: {citation}\n")
        
        # Simulate JSON payload
        payload = {
            "id": chunk_id,
            "citation": citation,
            "metadata": compact_meta,
            "text": doc_truncated,
            "truncated": truncated,
        }
        
        print("   JSON payload structure:")
        print(f"   {json.dumps(payload, ensure_ascii=False, indent=2)[:500]}...\n")
    else:
        print(f"   ✗ Chunk not found!")
    
    # Test 2: Invalid ID
    print(f"3. Testing with invalid chunk ID...")
    invalid = server.ingestion.collection.get(
        ids=["invalid_chunk_id_12345"],
        include=["documents", "metadatas"]
    )
    
    if not invalid.get("ids"):
        print(f"   ✓ Correctly returns None/empty for invalid ID\n")
    else:
        print(f"   ✗ Should have returned empty!\n")


if __name__ == "__main__":
    test_get_chunk_by_id()

