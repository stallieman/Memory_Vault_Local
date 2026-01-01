"""Test script to ask a single question and see the grounded answer."""
import sys
import os
from pathlib import Path

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ingestion import DocumentIngestion  # type: ignore
from local_rag_ollama import retrieve_context, ask_with_strict_validation, get_effective_model, check_ollama_connection  # type: ignore

# Test question
question = """create an index template for a dummy index, with dummy settings and mapping with different types.
I want to use this as a dummy template I can reuse and change when needed. Format it nicely. It is for kibana dev tools"""

print("=" * 80)
print("TESTING QUESTION")
print("=" * 80)
print(f"\nQuestion: {question}\n")

# Check Ollama
print("Checking Ollama connection...")
is_connected, available_models = check_ollama_connection()
if not is_connected:
    print("ERROR: Ollama is not running. Please start Ollama first.")
    sys.exit(1)

effective_model = get_effective_model(available_models)
print(f"OK - Using model: {effective_model}\n")

# Initialize KB
print("Initializing knowledge base...")
kb = DocumentIngestion()
stats = kb.get_stats()
print(f"OK - Knowledge base ready: {stats['total_chunks']} chunks\n")

# Retrieve context
print("Searching knowledge base...")
context_chunks, allowed_ids, diagnostics = retrieve_context(kb, question)

if not context_chunks:
    print("WARNING: No relevant results found in knowledge base.")
    sys.exit(0)

print(f"OK - Retrieved {diagnostics['final_count']} chunks")
if diagnostics.get('low_relevance_filtered', 0) > 0:
    print(f"  Filtered {diagnostics['low_relevance_filtered']} low-relevance chunks")
if diagnostics['toc_filtered'] > 0:
    print(f"  Filtered {diagnostics['toc_filtered']} TOC-like chunks")

print(f"\nTop sources:")
for chunk in context_chunks[:8]:
    meta = chunk["metadata"]
    source = meta.get("relative_path", meta.get("filename", "unknown"))
    print(f"  [{chunk['id']}] {source} (score: {chunk['score']:.3f})")

print(f"\nAsking {effective_model}...\n")

try:
    answer, used_citations = ask_with_strict_validation(
        question, context_chunks, allowed_ids, effective_model
    )
    
    print("=" * 80)
    print("SUCCESS - ANSWER VALIDATED:")
    print("=" * 80)
    print(answer)
    print("-" * 80)
    if used_citations:
        print(f"Citations: {', '.join(sorted(used_citations))}")
    print("=" * 80)
    
except Exception as e:
    print("=" * 80)
    print(f"ERROR: {e}")
    print("=" * 80)
