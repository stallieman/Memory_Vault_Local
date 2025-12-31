"""
Grounded Local RAG with Ollama + ChromaDB Knowledge Base
Citation-enforced Q&A using local Ollama LLM with C:\\Notes as knowledge base.

Features:
- Strict grounding: answers only from provided context
- Citation validation: [chunk:<id>] format required
- Retry logic: re-asks with stricter prompt on citation failure
- No hallucinated sources allowed
"""

import os
import re
import sys
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from ingestion import DocumentIngestion

# ============================================================================
# Configuration via environment variables
# ============================================================================
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "rag-grounded-nemo")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "4"))
RAG_TOP_K_FULL = int(os.environ.get("RAG_TOP_K_FULL", "2"))
RAG_MAX_CHARS_FULL = int(os.environ.get("RAG_MAX_CHARS_FULL", "4500"))
RAG_SNIPPET_CHARS = int(os.environ.get("RAG_SNIPPET_CHARS", "400"))
RAG_NUM_CTX = int(os.environ.get("RAG_NUM_CTX", "8192"))

# The exact "I don't know" response
IDK_RESPONSE = "I don't know based on the provided context."


# ============================================================================
# Ollama connectivity checks
# ============================================================================
def check_ollama_connection() -> Tuple[bool, List[str]]:
    """
    Check if Ollama is running and get available models.
    Returns (is_connected, list_of_model_names).
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return True, models
    except requests.exceptions.ConnectionError:
        return False, []
    except requests.exceptions.Timeout:
        return False, []
    except Exception as e:
        print(f"⚠ Unexpected error checking Ollama: {e}")
        return False, []


def get_effective_model(available_models: List[str]) -> str:
    """
    Get the effective model to use.
    Checks for exact match, then partial match, then falls back.
    """
    if OLLAMA_MODEL in available_models:
        return OLLAMA_MODEL
    
    # Check if the base model name (without tag) matches
    base_model = OLLAMA_MODEL.split(":")[0]
    for model in available_models:
        if model.startswith(base_model):
            print(f"⚠ Exact model '{OLLAMA_MODEL}' not found.")
            print(f"  Using similar model: '{model}'")
            return model
    
    # No matching model found
    print(f"⚠ Model '{OLLAMA_MODEL}' not found in Ollama.")
    if available_models:
        print(f"  Available models: {', '.join(available_models[:5])}")
        # Prefer a grounded model if available
        for m in available_models:
            if "grounded" in m.lower():
                print(f"  Using: '{m}'")
                return m
        print(f"  Using first available: '{available_models[0]}'")
        return available_models[0]
    
    print("✗ No models found in Ollama. Please pull a model first:")
    print(f"  ollama pull mistral-nemo:12b-instruct-2407-q4_K_M")
    print(f"  ollama create rag-grounded-nemo -f ollama/Modelfile.rag-grounded")
    return OLLAMA_MODEL


# ============================================================================
# Context building
# ============================================================================
def retrieve_context(kb: DocumentIngestion, question: str) -> Tuple[List[Dict], Set[str]]:
    """
    Retrieve relevant context chunks from the knowledge base.
    Returns (list_of_chunks, set_of_allowed_chunk_ids).
    
    Each chunk dict contains: text, metadata, id, score
    """
    result = kb.query(question, n_results=RAG_TOP_K)
    
    if not result["results"] or not result["results"]["ids"][0]:
        return [], set()
    
    documents = result["results"]["documents"][0]
    metadatas = result["results"]["metadatas"][0]
    distances = result["results"]["distances"][0]
    ids = result["results"]["ids"][0]

    context_chunks = []
    allowed_ids = set()
    
    for i, (doc, meta, dist, chunk_id) in enumerate(zip(documents, metadatas, distances, ids)):
        allowed_ids.add(chunk_id)
        
        # Only include full text for top RAG_TOP_K_FULL chunks
        if i < RAG_TOP_K_FULL:
            text = doc.strip()
            if len(text) > RAG_MAX_CHARS_FULL:
                text = text[:RAG_MAX_CHARS_FULL].rstrip() + "..."
        else:
            # Snippet only for remaining chunks
            text = doc.strip()
            if len(text) > RAG_SNIPPET_CHARS:
                text = text[:RAG_SNIPPET_CHARS].rstrip() + "..."
        
        context_chunks.append({
            "text": text,
            "metadata": meta,
            "id": chunk_id,
            "score": 1 - float(dist)
        })
    
    return context_chunks, allowed_ids


def build_context_payload(context_chunks: List[Dict]) -> str:
    """
    Build the CONTEXT text with explicit chunk labels.
    Format: [chunk:<id>] source=<filename>
    """
    parts = []
    for chunk in context_chunks:
        meta = chunk["metadata"]
        source = meta.get("relative_path", meta.get("filename", "unknown"))
        chunk_id = chunk["id"]
        
        header = f"[chunk:{chunk_id}] source={source}"
        parts.append(f"{header}\n{chunk['text']}")
    
    return "\n\n---\n\n".join(parts)


# ============================================================================
# Citation validation
# ============================================================================
def extract_citations(text: str) -> Set[str]:
    """
    Extract all [chunk:<id>] citations from the model output.
    Returns set of chunk IDs found.
    """
    pattern = r'\[chunk:([^\]]+)\]'
    matches = re.findall(pattern, text)
    return set(matches)


def validate_citations(
    answer: str, 
    allowed_ids: Set[str]
) -> Tuple[bool, str, Set[str], Set[str]]:
    """
    Validate that the answer contains proper citations.
    
    Returns: (is_valid, reason, found_citations, invalid_citations)
    """
    answer_stripped = answer.strip()
    
    # Check for exact IDK response
    if answer_stripped == IDK_RESPONSE:
        return True, "IDK response accepted", set(), set()
    
    # Extract citations
    found_citations = extract_citations(answer)
    
    # Check for at least one citation
    if not found_citations:
        return False, "No citations found in answer", set(), set()
    
    # Check all citations are valid
    invalid_citations = found_citations - allowed_ids
    if invalid_citations:
        return False, f"Invalid chunk IDs cited: {invalid_citations}", found_citations, invalid_citations
    
    return True, "Valid citations", found_citations, set()


# ============================================================================
# Ollama chat
# ============================================================================
def call_ollama(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.1
) -> Tuple[str, Optional[str]]:
    """
    Call Ollama /api/chat endpoint.
    Returns (response_text, error_message).
    """
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_ctx": RAG_NUM_CTX
                }
            },
            timeout=300
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"], None
    except requests.exceptions.ConnectionError:
        return "", "Cannot connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        return "", "Ollama request timed out."
    except Exception as e:
        return "", f"Ollama error: {str(e)}"


def ask_with_validation(
    question: str,
    context_chunks: List[Dict],
    allowed_ids: Set[str],
    model: str
) -> Tuple[str, bool, Set[str]]:
    """
    Ask the question with context and validate citations.
    Retries once with stricter prompt if validation fails.
    
    Returns: (answer, is_valid, used_citations)
    """
    context_text = build_context_payload(context_chunks)
    allowed_ids_str = ", ".join(sorted(allowed_ids))
    
    # Initial user message
    user_message = f"""CONTEXT:
{context_text}

ALLOWED CHUNK IDS: {allowed_ids_str}

QUESTION: {question}"""

    messages = [
        {"role": "user", "content": user_message}
    ]
    
    # First attempt
    answer, error = call_ollama(model, messages)
    if error:
        return f"Error: {error}", False, set()
    
    # Validate
    is_valid, reason, found_citations, invalid_citations = validate_citations(answer, allowed_ids)
    
    if is_valid:
        return answer, True, found_citations
    
    # Retry with stricter reminder
    print(f"  ⚠ Citation validation failed: {reason}")
    print(f"  🔄 Retrying with stricter prompt...")
    
    retry_message = f"""Your previous answer was rejected because: {reason}

REMINDER - STRICT RULES:
1. You MUST cite from these chunk IDs ONLY: {allowed_ids_str}
2. Use format [chunk:<id>] for every factual claim
3. If you cannot answer from the provided context, respond EXACTLY with: "{IDK_RESPONSE}"
4. Do NOT invent any sources, books, pages, or URLs

Please answer the question again using ONLY the provided CONTEXT.

QUESTION: {question}"""

    messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": retry_message})
    
    answer2, error2 = call_ollama(model, messages)
    if error2:
        return f"Error on retry: {error2}", False, set()
    
    # Validate retry
    is_valid2, reason2, found_citations2, _ = validate_citations(answer2, allowed_ids)
    
    if is_valid2:
        return answer2, True, found_citations2
    
    # Still invalid after retry - return with warning
    print(f"  ⚠ Still invalid after retry: {reason2}")
    return f"[WARNING: Answer may contain invalid citations]\n\n{answer2}", False, found_citations2


# ============================================================================
# Main interactive loop
# ============================================================================
def main():
    """Main interactive loop for grounded RAG Q&A."""
    print("=" * 70)
    print("Grounded Local RAG with Ollama + C:\\Notes")
    print("Citation-enforced answers from your knowledge base")
    print("=" * 70)
    
    # Check Ollama connection
    print("\n🔍 Checking Ollama connection...")
    is_connected, available_models = check_ollama_connection()
    
    if not is_connected:
        print("\n" + "=" * 70)
        print("✗ ERROR: Ollama is not running.")
        print()
        print("  Start Ollama Desktop or run: ollama serve")
        print()
        print("  If you haven't created the grounded model yet:")
        print("    ollama pull mistral-nemo:12b-instruct-2407-q4_K_M")
        print("    ollama create rag-grounded-nemo -f ollama\\Modelfile.rag-grounded")
        print("=" * 70)
        sys.exit(1)
    
    print(f"✓ Ollama is running at {OLLAMA_BASE_URL}")
    if available_models:
        print(f"  Available models: {', '.join(available_models[:5])}")
    
    # Determine effective model
    effective_model = get_effective_model(available_models)
    print(f"\n📦 Using model: {effective_model}")
    
    # Warn if not using grounded model
    if "grounded" not in effective_model.lower():
        print("\n⚠ WARNING: Not using a grounded model!")
        print("  For best results, create the grounded model:")
        print("    ollama create rag-grounded-nemo -f ollama\\Modelfile.rag-grounded")
    
    # Initialize knowledge base
    print("\n📚 Initializing knowledge base...")
    try:
        kb = DocumentIngestion()
    except Exception as e:
        print(f"✗ Error initializing knowledge base: {e}")
        sys.exit(1)
    
    stats = kb.get_stats()
    print(f"\n✓ Ready!")
    print(f"  - Data directory: {stats['data_directory']}")
    print(f"  - Database: {stats['total_chunks']} chunks indexed")
    print(f"  - Model: {effective_model}")
    print(f"  - Context: top {RAG_TOP_K} chunks ({RAG_TOP_K_FULL} full)")
    print("-" * 70)
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.")
    print("Answers will include [chunk:<id>] citations.\n")
    
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break

        if not question:
            continue
            
        if question.lower() in {"exit", "quit", "q"}:
            print("\n👋 Goodbye!")
            break

        print("\n🔍 Searching knowledge base...")
        context_chunks, allowed_ids = retrieve_context(kb, question)
        
        if not context_chunks:
            print("⚠ No relevant results found in knowledge base.\n")
            continue

        print(f"✓ Found {len(context_chunks)} relevant chunks.")
        print(f"  Allowed chunk IDs: {', '.join(sorted(allowed_ids))}")
        
        # Show sources
        print("  Sources:")
        for chunk in context_chunks:
            meta = chunk["metadata"]
            source = meta.get("relative_path", meta.get("filename", "unknown"))
            print(f"    - [{chunk['id']}] {source} (score: {chunk['score']:.2f})")
        
        print(f"\n🤖 Asking {effective_model}...")
        answer, is_valid, used_citations = ask_with_validation(
            question, context_chunks, allowed_ids, effective_model
        )
        
        print("\n" + "=" * 70)
        if is_valid:
            print("✓ Answer (validated):")
        else:
            print("⚠ Answer (validation failed):")
        print("-" * 70)
        print(answer)
        print("-" * 70)
        if used_citations:
            print(f"Citations used: {', '.join(sorted(used_citations))}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
