"""
Grounded Local RAG with Ollama + ChromaDB Knowledge Base
Citation-enforced Q&A using local Ollama LLM with C:\\Notes as knowledge base.

Features:
- Strict fail-fast grounding: answers only from provided context
- Citation validation: [chunk:<id>] format required
- Single retry with fail-fast on second failure
- Forbidden word detection for hallucinated sources
- No silent fallbacks - raises exceptions on invalid answers
"""

import os
import re
import sys
import json
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

# ============================================================================
# STRICT CITATION ENFORCEMENT CONSTANTS
# ============================================================================
# The EXACT "I don't know" response - must match character-for-character
IDK = "I don't know based on the provided context."

# Regex pattern for valid citations: [chunk:abc123_0001] or [chunk:def-456:0002]
CITATION_PATTERN = re.compile(r"\[chunk:([A-Za-z0-9_:-]+)\]")

# Forbidden words that indicate hallucinated external sources
# If these appear WITHOUT a valid [chunk:...] citation nearby, it's suspicious
FORBIDDEN_SOURCE_WORDS = {
    # Books/publications
    "chapter", "page", "pages", "isbn", "edition", "publisher",
    # Websites
    "baeldung", "stackoverflow", "medium.com", "dev.to", "wikipedia",
    "geeksforgeeks", "tutorialspoint", "w3schools",
    # Authors (common hallucination targets)
    "kleppmann", "martin fowler", "uncle bob", "robert martin",
    # Academic
    "et al", "proceedings", "journal", "arxiv",
}

# Compile pattern for forbidden words (case-insensitive)
FORBIDDEN_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in FORBIDDEN_SOURCE_WORDS) + r')\b',
    re.IGNORECASE
)


# ============================================================================
# Custom Exception for Citation Validation Failures
# ============================================================================
class CitationValidationError(ValueError):
    """Raised when answer fails citation validation after retry."""
    
    def __init__(self, reason: str, debug_payload: dict):
        self.reason = reason
        self.debug_payload = debug_payload
        super().__init__(f"Citation validation failed: {reason}")


# ============================================================================
# Debug Bundle Printer
# ============================================================================
def print_debug_bundle(debug_payload: dict) -> None:
    """Print complete debug information before raising exception."""
    print("\n" + "=" * 70)
    print("🚨 CITATION VALIDATION FAILURE - DEBUG BUNDLE")
    print("=" * 70)
    
    print(f"\n📦 Model: {debug_payload.get('model', 'unknown')}")
    
    print(f"\n📋 Allowed Chunk IDs ({len(debug_payload.get('allowed_ids', []))}):")
    for cid in sorted(debug_payload.get('allowed_ids', [])):
        print(f"    - {cid}")
    
    print(f"\n📤 User Prompt Sent:")
    print("-" * 70)
    user_prompt = debug_payload.get('user_prompt', '')
    # Truncate if very long
    if len(user_prompt) > 3000:
        print(user_prompt[:3000])
        print(f"\n... [truncated, {len(user_prompt)} chars total]")
    else:
        print(user_prompt)
    print("-" * 70)
    
    print(f"\n📥 Raw Model Output:")
    print("-" * 70)
    print(debug_payload.get('model_output', ''))
    print("-" * 70)
    
    print(f"\n❌ Failure Reason: {debug_payload.get('reason', 'unknown')}")
    
    if debug_payload.get('found_citations'):
        print(f"\n🔍 Citations Found: {debug_payload.get('found_citations')}")
    if debug_payload.get('invalid_citations'):
        print(f"🚫 Invalid Citations: {debug_payload.get('invalid_citations')}")
    if debug_payload.get('forbidden_words_found'):
        print(f"⚠️  Forbidden Words Found: {debug_payload.get('forbidden_words_found')}")
    
    print("\n" + "=" * 70)


# ============================================================================
# STRICT Citation Validation (Fail-Fast)
# ============================================================================
def validate_answer(
    text: str,
    allowed_ids: Set[str],
    debug_payload: dict
) -> Set[str]:
    """
    Validate that an answer contains proper citations.
    
    FAIL-FAST: Raises CitationValidationError if validation fails.
    
    Args:
        text: The model's response text
        allowed_ids: Set of valid chunk IDs from the context
        debug_payload: Dict with debug info (model, user_prompt, etc.)
    
    Returns:
        Set of valid citation IDs found (only if validation passes)
    
    Raises:
        CitationValidationError: If validation fails for any reason
    """
    text_stripped = text.strip()
    
    # ACCEPT: Exact IDK response
    if text_stripped == IDK:
        return set()  # No citations needed for IDK
    
    # Extract all citations
    found_citations = set(CITATION_PATTERN.findall(text))
    
    # FAIL: No citations found
    if not found_citations:
        debug_payload['reason'] = "No citations found"
        debug_payload['model_output'] = text
        debug_payload['found_citations'] = set()
        print_debug_bundle(debug_payload)
        raise CitationValidationError("No citations found", debug_payload)
    
    # FAIL: Unknown citation IDs
    invalid_citations = found_citations - allowed_ids
    if invalid_citations:
        debug_payload['reason'] = f"Unknown citation ids: {invalid_citations}"
        debug_payload['model_output'] = text
        debug_payload['found_citations'] = found_citations
        debug_payload['invalid_citations'] = invalid_citations
        print_debug_bundle(debug_payload)
        raise CitationValidationError(
            f"Unknown citation ids: {invalid_citations}", 
            debug_payload
        )
    
    # WARN/FAIL: Forbidden words detected (potential hallucination)
    forbidden_matches = FORBIDDEN_PATTERN.findall(text.lower())
    if forbidden_matches:
        # Check if these forbidden words appear near a citation
        # For now, just warn but don't fail (could be legitimate context)
        unique_forbidden = set(forbidden_matches)
        debug_payload['forbidden_words_found'] = unique_forbidden
        print(f"  ⚠️  Warning: Potential external sources mentioned: {unique_forbidden}")
        # Uncomment to make this a hard failure:
        # debug_payload['reason'] = f"Forbidden source words found: {unique_forbidden}"
        # debug_payload['model_output'] = text
        # debug_payload['found_citations'] = found_citations
        # print_debug_bundle(debug_payload)
        # raise CitationValidationError(f"Forbidden source words: {unique_forbidden}", debug_payload)
    
    # SUCCESS: All citations are valid
    return found_citations


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


# ============================================================================
# STRICT Fail-Fast Ask with Validation
# ============================================================================
def ask_with_strict_validation(
    question: str,
    context_chunks: List[Dict],
    allowed_ids: Set[str],
    model: str
) -> Tuple[str, Set[str]]:
    """
    Ask the question with context and STRICTLY validate citations.
    
    FAIL-FAST: Raises CitationValidationError if validation fails after retry.
    No silent fallbacks, no warnings-only - either valid or exception.
    
    Args:
        question: User's question
        context_chunks: Retrieved context chunks
        allowed_ids: Set of valid chunk IDs
        model: Ollama model name
    
    Returns:
        Tuple of (validated_answer, used_citations)
    
    Raises:
        CitationValidationError: If answer fails validation after retry
        RuntimeError: If Ollama returns an error
    """
    context_text = build_context_payload(context_chunks)
    allowed_ids_str = ", ".join(sorted(allowed_ids))
    
    # Build the user prompt
    user_prompt = f"""CONTEXT:
{context_text}

ALLOWED CHUNK IDS: {allowed_ids_str}

QUESTION: {question}"""

    messages = [
        {"role": "user", "content": user_prompt}
    ]
    
    # Prepare debug payload (will be filled on failure)
    debug_payload = {
        "model": model,
        "allowed_ids": allowed_ids,
        "user_prompt": user_prompt,
        "question": question,
    }
    
    # ========== FIRST ATTEMPT ==========
    answer, error = call_ollama(model, messages)
    if error:
        raise RuntimeError(f"Ollama error: {error}")
    
    # Try to validate
    try:
        used_citations = validate_answer(answer, allowed_ids, debug_payload.copy())
        return answer, used_citations  # SUCCESS on first try
    except CitationValidationError as e:
        # First attempt failed - will retry
        first_failure_reason = e.reason
        print(f"  ⚠️  First attempt failed: {first_failure_reason}")
        print(f"  🔄 Retrying with stricter prompt...")
    
    # ========== SINGLE RETRY ==========
    retry_prompt = f"""Your previous answer was REJECTED because: {first_failure_reason}

⚠️ STRICT RULES - YOU MUST FOLLOW:
1. Cite ONLY from these chunk IDs: {allowed_ids_str}
2. Use EXACT format [chunk:<id>] for EVERY factual claim
3. If you CANNOT answer from the CONTEXT, respond EXACTLY with:
   "{IDK}"
4. Do NOT mention ANY external sources (books, websites, authors, pages)

Answer the question again using ONLY the provided CONTEXT.

QUESTION: {question}"""

    messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": retry_prompt})
    
    # Update debug payload with retry info
    debug_payload['retry_prompt'] = retry_prompt
    debug_payload['first_answer'] = answer
    debug_payload['first_failure_reason'] = first_failure_reason
    
    answer2, error2 = call_ollama(model, messages)
    if error2:
        raise RuntimeError(f"Ollama error on retry: {error2}")
    
    # ========== VALIDATE RETRY (FAIL-FAST) ==========
    # This will raise CitationValidationError if invalid
    used_citations = validate_answer(answer2, allowed_ids, debug_payload)
    
    return answer2, used_citations  # SUCCESS on retry


# ============================================================================
# Main interactive loop
# ============================================================================
def main():
    """Main interactive loop for grounded RAG Q&A."""
    print("=" * 70)
    print("Grounded Local RAG with Ollama + C:\\Notes")
    print("STRICT Citation Enforcement - Fail-Fast Mode")
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
        print("\n⚠️  WARNING: Not using a grounded model!")
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
    print(f"\n✓ Ready! (STRICT MODE)")
    print(f"  - Data directory: {stats['data_directory']}")
    print(f"  - Database: {stats['total_chunks']} chunks indexed")
    print(f"  - Model: {effective_model}")
    print(f"  - Context: top {RAG_TOP_K} chunks ({RAG_TOP_K_FULL} full)")
    print(f"  - Citation enforcement: FAIL-FAST (no invalid answers allowed)")
    print("-" * 70)
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.")
    print("All answers MUST include valid [chunk:<id>] citations or will be rejected.\n")
    
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
            print("⚠️  No relevant results found in knowledge base.\n")
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
        
        try:
            # STRICT validation - will raise exception if invalid
            answer, used_citations = ask_with_strict_validation(
                question, context_chunks, allowed_ids, effective_model
            )
            
            # SUCCESS - answer is validated
            print("\n" + "=" * 70)
            print("✅ Answer (VALIDATED):")
            print("-" * 70)
            print(answer)
            print("-" * 70)
            if used_citations:
                print(f"📎 Citations: {', '.join(sorted(used_citations))}")
            elif answer.strip() == IDK:
                print("ℹ️  Response: I don't know (no citations needed)")
            print("=" * 70 + "\n")
            
        except CitationValidationError as e:
            # FAIL-FAST: Citation validation failed after retry
            print("\n" + "=" * 70)
            print("❌ ANSWER REJECTED - Citation validation failed")
            print(f"   Reason: {e.reason}")
            print("=" * 70)
            print("\nThe model failed to provide a properly cited answer.")
            print("This could mean:")
            print("  - The context doesn't contain relevant information")
            print("  - The model is hallucinating sources")
            print("  - The grounded model isn't properly configured")
            print("\nTry rephrasing your question or check if the topic is in your notes.\n")
            
        except RuntimeError as e:
            # Ollama connection error
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
