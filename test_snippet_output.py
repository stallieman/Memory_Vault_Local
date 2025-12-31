#!/usr/bin/env python3
"""Test script for snippet-only query output."""

import sys
sys.path.insert(0, 'src')

from server import KnowledgeBaseMCPServer

def test_snippet_output():
    """Test query with snippet-only output."""
    print("=== Testing Snippet-Only Query Output ===\n")
    
    server = KnowledgeBaseMCPServer()
    result = server.ingestion.query("git stash", n_results=2)
    
    print(f"Found {result['count']} results\n")
    
    # Simulate snippet-only output (default behavior)
    print("--- Default Output (snippets only) ---\n")
    for rank, (doc, metadata, distance, doc_id) in enumerate(zip(
        result['results']['documents'][0],
        result['results']['metadatas'][0],
        result['results']['distances'][0],
        result['results']['ids'][0]
    ), 1):
        from server import format_citation, make_snippet
        
        citation = format_citation(metadata)
        score = 1 - float(distance)
        snippet = make_snippet(doc, 400)  # Default snippet size
        
        print(f"## Resultaat {rank}")
        print(f"**ID:** `{doc_id}`")
        print(f"**Cite:** {citation}")
        print(f"**Score:** {score:.2%}\n")
        print(f"{snippet}\n")
        print("---\n")
    
    # Simulate with full text included
    print("\n--- With include_full_text=True ---\n")
    doc = result['results']['documents'][0][0]
    metadata = result['results']['metadatas'][0][0]
    doc_id = result['results']['ids'][0][0]
    
    from server import format_citation, make_snippet
    
    citation = format_citation(metadata)
    score = 1 - float(result['results']['distances'][0][0])
    snippet = make_snippet(doc, 400)
    
    full = doc.strip()
    if len(full) > 1500:
        full = full[:1500].rstrip() + "…"
    
    print(f"## Resultaat 1")
    print(f"**ID:** `{doc_id}`")
    print(f"**Cite:** {citation}")
    print(f"**Score:** {score:.2%}\n")
    print(f"{snippet}\n")
    print("<details><summary>Full text</summary>\n")
    print(f"{full}\n")
    print("</details>\n")
    print("---\n")
    
    # Compare sizes
    snippet_len = len(snippet)
    full_len = len(full)
    
    print(f"\n=== Size Comparison ===")
    print(f"Snippet: {snippet_len} chars")
    print(f"Full text: {full_len} chars")
    print(f"Reduction: {(1 - snippet_len/full_len)*100:.1f}%")


if __name__ == "__main__":
    test_snippet_output()
