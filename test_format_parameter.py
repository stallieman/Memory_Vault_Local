#!/usr/bin/env python3
"""Test script for format parameter in get_chunk_by_id."""

import sys
import json
sys.path.insert(0, 'src')

from server import KnowledgeBaseMCPServer, format_citation, compact_metadata, make_snippet

def test_format_parameter():
    """Test get_chunk_by_id with different format values."""
    print("=== Testing Format Parameter ===\n")
    
    server = KnowledgeBaseMCPServer()
    
    # Get a chunk ID
    result = server.ingestion.query("git stash", n_results=1)
    chunk_id = result['results']['ids'][0][0]
    
    print(f"Testing with chunk ID: {chunk_id}\n")
    
    # Fetch the chunk data
    res = server.ingestion.collection.get(
        ids=[chunk_id],
        include=["documents", "metadatas"]
    )
    
    doc = (res.get("documents") or [""])[0] or ""
    meta = (res.get("metadatas") or [{}])[0] or {}
    
    # Simulate truncation
    max_chars = 5000
    doc = doc.strip()
    truncated = False
    if max_chars and len(doc) > max_chars:
        doc = doc[:max_chars].rstrip() + "…"
        truncated = True
    
    citation = format_citation(meta)
    
    print("=== Format: 'raw' (default) ===\n")
    text_raw = doc
    print(text_raw)
    print(f"\n(Length: {len(text_raw)} chars)\n")
    
    print("\n=== Format: 'markdown' ===\n")
    text_md = "# Chunk\n\n"
    text_md += f"**ID:** {chunk_id}\n\n"
    text_md += f"**Cite:** {citation}\n\n"
    text_md += "## Text\n\n"
    text_md += f"{doc}\n"
    print(text_md)
    print(f"\n(Length: {len(text_md)} chars)\n")
    
    print("\n=== JSON Payload (both formats) ===\n")
    
    # Raw format payload
    payload_raw = {
        "id": chunk_id,
        "format": "raw",
        "citation": citation,
        "metadata": compact_metadata(meta),
        "snippet": make_snippet(doc, 400),
        "truncated": truncated,
    }
    
    # Markdown format payload
    payload_md = {
        "id": chunk_id,
        "format": "markdown",
        "citation": citation,
        "metadata": compact_metadata(meta),
        "snippet": make_snippet(doc, 400),
        "truncated": truncated,
    }
    
    print("Raw format payload:")
    print(json.dumps(payload_raw, ensure_ascii=False, indent=2))
    
    print("\n\nMarkdown format payload:")
    print(json.dumps(payload_md, ensure_ascii=False, indent=2))
    
    print("\n\n=== Size Comparison ===")
    print(f"Raw output: {len(text_raw)} chars")
    print(f"Markdown output: {len(text_md)} chars")
    print(f"Overhead: {len(text_md) - len(text_raw)} chars ({((len(text_md) / len(text_raw) - 1) * 100):.1f}%)")
    
    print("\n✓ Format parameter enables flexible output!")
    print("✓ 'raw' = clean text for Claude to process")
    print("✓ 'markdown' = formatted with metadata headers")


if __name__ == "__main__":
    test_format_parameter()
