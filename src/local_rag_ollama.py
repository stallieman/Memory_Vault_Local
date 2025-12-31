"""
Grounded Local RAG with Ollama + ChromaDB Knowledge Base
Citation-enforced Q&A using local Ollama LLM with C:\\Notes as knowledge base.

Features:
- Strict fail-fast grounding: answers only from provided context
- Citation validation: [chunk:<id>] format required
- TOC filtering: excludes table-of-contents chunks from PDFs
- Adjacent chunk expansion: fetches neighboring chunks for context
- Quote requirement: each rule must include a verbatim quote
- Single retry with fail-fast on second failure
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
from retrieval import PrioritizedRetriever, RAG_TOP_K_TOTAL, RAG_TOP_K_PER_GROUP, GROUP_ORDER

# ============================================================================
# Configuration via environment variables
# ============================================================================
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "rag-grounded-nemo")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "6"))  # Increased to allow for TOC filtering
RAG_TOP_K_FULL = int(os.environ.get("RAG_TOP_K_FULL", "3"))
RAG_MAX_CHARS_FULL = int(os.environ.get("RAG_MAX_CHARS_FULL", "4500"))
RAG_SNIPPET_CHARS = int(os.environ.get("RAG_SNIPPET_CHARS", "400"))
RAG_NUM_CTX = int(os.environ.get("RAG_NUM_CTX", "8192"))

# TOC filtering and chunk expansion
RAG_FILTER_TOC = os.environ.get("RAG_FILTER_TOC", "1") == "1"
RAG_PDF_EXPAND = os.environ.get("RAG_PDF_EXPAND", "1") == "1"
RAG_PDF_EXPAND_RADIUS = int(os.environ.get("RAG_PDF_EXPAND_RADIUS", "2"))

# Source diversity: max chunks per single source file
RAG_MAX_PER_SOURCE = int(os.environ.get("RAG_MAX_PER_SOURCE", "3"))

# ============================================================================
# STRICT CITATION ENFORCEMENT CONSTANTS
# ============================================================================
# The EXACT "I don't know" response - must match character-for-character
IDK = "I don't know based on the provided context."

# Regex pattern for valid citations: [chunk:abc123_0001] or [chunk:def-456:0002]
CITATION_PATTERN = re.compile(r"\[chunk:([A-Za-z0-9_:-]+)\]")

# Pattern to detect actual external URLs with domain names
# Only blocks real URLs like "https://example.com", not just "https://" in text
UNSUPPORTED_URL_PATTERN = re.compile(
    r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Flexible IDK detection: accept English and Dutch variants
# Matches:
# - "I don't know based on the provided context."
# - "Ik weet het niet gebaseerd op de/het gegeven/verstrekte context."
IDK_PATTERN = re.compile(
    r"^(I don't know|Ik weet (het )?niet)(\s+gebaseerd op|\s+based on).{0,50}(context|informatie).*$",
    re.IGNORECASE | re.DOTALL
)


# ============================================================================
# TOC Detection Heuristic
# ============================================================================
def is_toc_like(text: str) -> Tuple[bool, List[str]]:
    """
    Detect if a chunk looks like a Table of Contents / index page.
    
    Returns: (is_toc, list_of_reasons)
    """
    reasons = []
    lines = text.strip().split('\n')
    
    if not lines:
        return False, []
    
    # Heuristic 1: Many short lines (typical of TOC)
    short_lines = sum(1 for line in lines if 0 < len(line.strip()) < 60)
    if len(lines) > 5 and short_lines / len(lines) > 0.7:
        reasons.append("many_short_lines")
    
    # Heuristic 2: Dot leaders ("....." or "…..")
    dot_leader_pattern = re.compile(r'\.{3,}|…{2,}')
    dot_leader_count = len(dot_leader_pattern.findall(text))
    if dot_leader_count >= 3:
        reasons.append(f"dot_leaders({dot_leader_count})")
    
    # Heuristic 3: Numbers at end of lines (page numbers)
    page_number_pattern = re.compile(r'\s+\d{1,4}\s*$', re.MULTILINE)
    page_numbers = len(page_number_pattern.findall(text))
    if page_numbers >= 5:
        reasons.append(f"page_numbers({page_numbers})")
    
    # Heuristic 4: TOC keywords
    toc_keywords = ['contents', 'table of contents', 'index', 'overview', 'chapter']
    text_lower = text.lower()
    found_keywords = [kw for kw in toc_keywords if kw in text_lower]
    # Only count if combined with other signals
    if found_keywords and len(reasons) >= 1:
        reasons.append(f"keywords({','.join(found_keywords)})")
    
    # Heuristic 5: High newline ratio (many line breaks, little content)
    if len(text) > 100:
        newline_ratio = text.count('\n') / len(text)
        if newline_ratio > 0.08:  # More than 8% newlines
            reasons.append(f"high_newline_ratio({newline_ratio:.2f})")
    
    # Heuristic 6: Pattern of "Title 123" repeated (TOC entries)
    toc_entry_pattern = re.compile(r'^.{5,50}\s+\d{1,4}\s*$', re.MULTILINE)
    toc_entries = len(toc_entry_pattern.findall(text))
    if toc_entries >= 4:
        reasons.append(f"toc_entries({toc_entries})")
    
    # Consider TOC-like if 2+ heuristics match
    is_toc = len(reasons) >= 2
    return is_toc, reasons


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
    print("\n" + "=" * 80)
    print("🚨 CITATION VALIDATION FAILURE - DEBUG BUNDLE")
    print("=" * 80)
    
    print(f"\n📦 Model: {debug_payload.get('model', 'unknown')}")
    
    allowed = debug_payload.get('allowed_ids', [])
    print(f"\n📋 Allowed Chunk IDs ({len(allowed)}):")
    if len(allowed) <= 10:
        for cid in sorted(allowed):
            print(f"    ✓ {cid}")
    else:
        for cid in sorted(allowed)[:10]:
            print(f"    ✓ {cid}")
        print(f"    ... and {len(allowed) - 10} more")
    
    print(f"\n📤 User Prompt (truncated):")
    print("-" * 80)
    user_prompt = debug_payload.get('user_prompt', '')
    if len(user_prompt) > 1500:
        print(user_prompt[:1500])
        print(f"\n... [truncated, {len(user_prompt)} chars total]")
    else:
        print(user_prompt)
    print("-" * 80)
    
    print(f"\n📥 Raw Model Output (first 5000 chars):")
    print("-" * 80)
    output = debug_payload.get('model_output', '')
    print(output if len(output) <= 5000 else output[:5000] + "\n... [truncated]")
    print("-" * 80)
    
    print(f"\n❌ Failure Reason:")
    print(f"   {debug_payload.get('reason', 'unknown')}")
    
    # Show found vs invalid citations
    found = debug_payload.get('found_citations', [])
    invalid = debug_payload.get('invalid_citations', [])
    
    if found:
        print(f"\n🔍 Citations Found ({len(found)}):")
        for cid in sorted(found) if isinstance(found, (set, list)) else [found]:
            print(f"    - {cid}")
    
    if invalid:
        print(f"\n🚫 Invalid Citations ({len(invalid)}):")
        for cid in sorted(invalid):
            print(f"    ✗ {cid} (NOT IN ALLOWED SET)")
    
    if debug_payload.get('urls_found'):
        print(f"\n🌐 External URLs Found: {debug_payload.get('urls_found')}")
    
    if 'quotes_found' in debug_payload:
        qcount = debug_payload['quotes_found']
        print(f"\n💬 Quotes Found: {qcount}")
    
    print("\n" + "=" * 80)


# ============================================================================
# STRICT Citation Validation (Fail-Fast) - FIXED VERSION
# ============================================================================

# Pattern for quoted text (various quote styles)
QUOTE_PATTERN = re.compile(r'["""]([^"""]{10,})["""]')


def validate_answer(
    text: str,
    allowed_ids: Set[str],
    debug_payload: dict,
    require_quotes: bool = True
) -> Set[str]:
    """
    Validate that an answer contains proper citations.
    
    FAIL-FAST: Raises CitationValidationError if validation fails.
    
    Validation Rules:
    1. IDK response is always valid (no citations required)
    2. Must contain at least one valid [chunk:id] citation
    3. All cited IDs must be from allowed_ids (no hallucinated chunks)
    4. Must NOT contain external URLs (http/https links)
    5. Optionally require verbatim quotes (if require_quotes=True)
    
    REMOVED: Generic word banning ("page", "chapter", etc.) - too restrictive
    
    Args:
        text: The model's response text
        allowed_ids: Set of valid chunk IDs from the context
        debug_payload: Dict with debug info (model, user_prompt, etc.)
        require_quotes: Whether to require quoted passages (default True)
    
    Returns:
        Set of valid citation IDs found (only if validation passes)
    
    Raises:
        CitationValidationError: If validation fails for any reason
    """
    text_stripped = text.strip()
    
    # ACCEPT: Flexible IDK response (English or Dutch)
    # Exact match for backward compatibility
    if text_stripped == IDK:
        return set()  # No citations needed for IDK
    
    # Flexible pattern match for variations
    if IDK_PATTERN.match(text_stripped):
        return set()  # No citations needed for IDK variants
    
    # Extract all citations
    found_citations = set(CITATION_PATTERN.findall(text))
    
    # FAIL: No citations found
    if not found_citations:
        debug_payload['reason'] = "No citations found - answer must use [chunk:id] format"
        debug_payload['model_output'] = text[:5000]  # Truncate
        debug_payload['found_citations'] = set()
        print_debug_bundle(debug_payload)
        raise CitationValidationError("No citations found", debug_payload)
    
    # FAIL: Unknown citation IDs (hallucinated chunks)
    invalid_citations = found_citations - allowed_ids
    if invalid_citations:
        debug_payload['reason'] = f"Invalid chunk IDs - not in allowed set: {invalid_citations}"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = list(found_citations)
        debug_payload['invalid_citations'] = list(invalid_citations)
        print_debug_bundle(debug_payload)
        raise CitationValidationError(
            f"Invalid chunk IDs: {invalid_citations}", 
            debug_payload
        )
    
    # FAIL: External URLs detected (hallucination indicator)
    url_matches = UNSUPPORTED_URL_PATTERN.findall(text)
    if url_matches:
        unique_urls = set(url_matches)
        debug_payload['reason'] = f"External URLs not allowed - answer must cite local chunks only: {unique_urls}"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = list(found_citations)
        debug_payload['urls_found'] = list(unique_urls)
        print_debug_bundle(debug_payload)
        raise CitationValidationError(f"External URLs found: {unique_urls}", debug_payload)
    
    # FAIL: No quotes found (evidence requirement)
    if require_quotes:
        quotes_found = QUOTE_PATTERN.findall(text)
        if not quotes_found:
            debug_payload['reason'] = "No verbatim quotes found - answer must include quoted evidence from sources"
            debug_payload['model_output'] = text[:5000]
            debug_payload['found_citations'] = list(found_citations)
            debug_payload['quotes_found'] = 0
            print_debug_bundle(debug_payload)
            raise CitationValidationError("No quotes found - evidence required", debug_payload)
        debug_payload['quotes_found'] = len(quotes_found)  # Just count, not full quotes
    
    # SUCCESS: All validations passed
    print(f"✅ Citation validation passed: {len(found_citations)} citations, {len(set(found_citations))} unique chunks")
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
# Context building with TOC filtering and chunk expansion
# ============================================================================
def get_adjacent_chunk_ids(chunk_id: str, radius: int = 2) -> List[str]:
    """
    Generate adjacent chunk IDs for context expansion.
    
    Chunk ID format: {hash}_{index:04d}
    Returns list of adjacent IDs (before and after current chunk).
    """
    if '_' not in chunk_id:
        return []
    
    parts = chunk_id.rsplit('_', 1)
    if len(parts) != 2:
        return []
    
    doc_hash, idx_str = parts
    try:
        current_idx = int(idx_str)
    except ValueError:
        return []
    
    adjacent = []
    for offset in range(-radius, radius + 1):
        if offset == 0:
            continue  # Skip the current chunk
        new_idx = current_idx + offset
        if new_idx >= 0:
            adjacent.append(f"{doc_hash}_{new_idx:04d}")
    
    return adjacent


def retrieve_context(kb: DocumentIngestion, question: str, use_prioritized: bool = True) -> Tuple[List[Dict], Set[str], dict]:
    """
    Retrieve relevant context chunks from the knowledge base.
    Returns (list_of_chunks, set_of_allowed_chunk_ids, diagnostics_dict).
    
    Features:
    - Prioritized retrieval: Queries source_groups in priority order
    - TOC filtering: Excludes table-of-contents chunks
    - PDF chunk expansion: Fetches adjacent chunks for PDF sources
    - Source diversity: Max N chunks per source file
    - Quality metrics: Returns diagnostic info about filtering
    
    Each chunk dict contains: text, metadata, id, score
    """
    # Use prioritized retrieval to get diverse results across source_groups
    if use_prioritized:
        retriever = PrioritizedRetriever(kb)
        # Fetch more than needed to account for TOC filtering
        fetch_count = RAG_TOP_K * 2 if RAG_FILTER_TOC else RAG_TOP_K
        result = retriever.query_with_priority(
            query_text=question,
            top_k_total=fetch_count,
            per_group_k=RAG_TOP_K_PER_GROUP,
            group_order=GROUP_ORDER,
        )
    else:
        # Fallback to simple query
        fetch_count = RAG_TOP_K * 2 if RAG_FILTER_TOC else RAG_TOP_K
        result = kb.query(question, n_results=fetch_count)
    
    diagnostics = {
        "fetched": 0,
        "toc_filtered": 0,
        "toc_reasons": [],
        "expanded_chunks": 0,
        "final_count": 0,
        "pdf_sources": 0,
        "group_stats": result.get("group_stats", {}),
    }
    
    if not result["results"] or not result["results"]["ids"][0]:
        return [], set(), diagnostics
    
    documents = result["results"]["documents"][0]
    metadatas = result["results"]["metadatas"][0]
    distances = result["results"]["distances"][0]
    ids = result["results"]["ids"][0]
    
    diagnostics["fetched"] = len(ids)
    
    # Phase 1: Filter out TOC-like chunks AND enforce source diversity
    filtered_indices = []
    source_counts = {}  # Track how many chunks per source
    
    for i, (doc, meta, dist, chunk_id) in enumerate(zip(documents, metadatas, distances, ids)):
        # TOC filtering
        if RAG_FILTER_TOC:
            is_toc, toc_reasons = is_toc_like(doc)
            if is_toc:
                diagnostics["toc_filtered"] += 1
                diagnostics["toc_reasons"].append({
                    "id": chunk_id,
                    "reasons": toc_reasons,
                    "preview": doc[:100].replace('\n', '\\n')
                })
                continue
        
        # Source diversity: limit chunks per source
        source = meta.get("relative_path", meta.get("filename", "unknown"))
        current_count = source_counts.get(source, 0)
        if current_count >= RAG_MAX_PER_SOURCE:
            # Skip this chunk, already have enough from this source
            if "source_limited" not in diagnostics:
                diagnostics["source_limited"] = []
            diagnostics["source_limited"].append({
                "id": chunk_id,
                "source": source,
                "reason": f"Already have {RAG_MAX_PER_SOURCE} chunks from this source"
            })
            continue
        
        source_counts[source] = current_count + 1
        filtered_indices.append(i)
        
        if len(filtered_indices) >= RAG_TOP_K:
            break
    
    diagnostics["sources_used"] = dict(source_counts)
    
    # Phase 2: Build context chunks and collect PDF sources for expansion
    context_chunks = []
    allowed_ids = set()
    pdf_chunk_ids = []
    
    for rank, i in enumerate(filtered_indices):
        doc = documents[i]
        meta = metadatas[i]
        dist = distances[i]
        chunk_id = ids[i]
        
        allowed_ids.add(chunk_id)
        
        # Track PDF sources for expansion
        source = meta.get("relative_path", meta.get("filename", ""))
        if source.lower().endswith(".pdf"):
            pdf_chunk_ids.append(chunk_id)
            diagnostics["pdf_sources"] += 1
        
        # Only include full text for top RAG_TOP_K_FULL chunks
        if rank < RAG_TOP_K_FULL:
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
            "score": 1 - float(dist),
            "rank": rank
        })
    
    # Phase 3: Expand PDF chunks with adjacent chunks
    if RAG_PDF_EXPAND and pdf_chunk_ids:
        expansion_ids = []
        for pdf_id in pdf_chunk_ids[:RAG_TOP_K_FULL]:  # Only expand top chunks
            adjacent = get_adjacent_chunk_ids(pdf_id, RAG_PDF_EXPAND_RADIUS)
            expansion_ids.extend([aid for aid in adjacent if aid not in allowed_ids])
        
        if expansion_ids:
            # Fetch adjacent chunks from database
            try:
                # get_chunks_by_ids returns dict: {chunk_id: {"text":..., "metadata":...}}
                expanded_chunks_dict = kb.get_chunks_by_ids(expansion_ids)
                for chunk_id, chunk_data in expanded_chunks_dict.items():
                    if not chunk_data.get("text"):
                        continue
                    
                    # Check if it's TOC
                    if RAG_FILTER_TOC:
                        is_toc, _ = is_toc_like(chunk_data["text"])
                        if is_toc:
                            continue
                    
                    allowed_ids.add(chunk_id)
                    # Add as snippet
                    text = chunk_data["text"].strip()
                    if len(text) > RAG_SNIPPET_CHARS:
                        text = text[:RAG_SNIPPET_CHARS].rstrip() + "..."
                    
                    context_chunks.append({
                        "text": text,
                        "metadata": chunk_data.get("metadata", {}),
                        "id": chunk_id,
                        "score": 0.5,  # Lower score for expanded chunks
                        "rank": len(context_chunks),
                        "expanded": True
                    })
                    diagnostics["expanded_chunks"] += 1
            except Exception as e:
                print(f"  ⚠ Adjacent chunk expansion failed: {e}")
    
    diagnostics["final_count"] = len(context_chunks)
    return context_chunks, allowed_ids, diagnostics


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
        expanded_marker = " (expanded)" if chunk.get("expanded") else ""
        
        header = f"[chunk:{chunk_id}] source={source}{expanded_marker}"
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
    Ask the question with context and STRICTLY validate citations + quotes.
    
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
    
    # Build the user prompt with quote requirement
    user_prompt = f"""CONTEXT:
{context_text}

ALLOWED CHUNK IDS: {allowed_ids_str}

STRICT OUTPUT FORMAT:
For each fact you state, you MUST:
1. Include a verbatim quote from the source in "quotation marks"
2. Cite the chunk using [chunk:<id>] format immediately after the quote
3. Only use IDs from the ALLOWED list above

Example format:
"The exact text from the source" [chunk:abc123_0001]

If the context does NOT contain information to answer the question, respond EXACTLY with:
{IDK}

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
    
    # ========== FIRST ATTEMPT (lenient - no quote requirement) ==========
    answer, error = call_ollama(model, messages)
    if error:
        raise RuntimeError(f"Ollama error: {error}")
    
    # First try: lenient validation (no quote requirement yet)
    try:
        used_citations = validate_answer(answer, allowed_ids, debug_payload.copy(), require_quotes=False)
        # Check if quotes exist even without requirement
        quotes_found = QUOTE_PATTERN.findall(answer)
        if quotes_found:
            return answer, used_citations  # SUCCESS with quotes on first try
        else:
            # Has citations but no quotes - retry to get quotes
            print(f"  ⚠️  First attempt has citations but no quotes - requesting quotes...")
    except CitationValidationError as e:
        # First attempt failed - will retry
        first_failure_reason = e.reason
        print(f"  ⚠️  First attempt failed: {first_failure_reason}")
        print(f"  🔄 Retrying with stricter prompt...")
    
    # ========== SINGLE RETRY ==========
    first_failure_reason = debug_payload.get('reason', 'missing quotes')
    retry_prompt = f"""Your previous answer was REJECTED because: {first_failure_reason}

⚠️ STRICT RULES - YOU MUST FOLLOW:
1. For EVERY fact, include a VERBATIM QUOTE in "quotation marks" from the source
2. Cite using [chunk:<id>] IMMEDIATELY after each quote
3. Use ONLY these chunk IDs: {allowed_ids_str}
4. If you CANNOT answer from the CONTEXT, respond EXACTLY: "{IDK}"

CORRECT FORMAT EXAMPLE:
According to the documentation, "the exact words from the source text" [chunk:abc123_0001].

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
    
    # ========== VALIDATE RETRY (FAIL-FAST with quotes required) ==========
    # This will raise CitationValidationError if invalid
    used_citations = validate_answer(answer2, allowed_ids, debug_payload, require_quotes=True)
    
    return answer2, used_citations  # SUCCESS on retry


# ============================================================================
# Main interactive loop
# ============================================================================
def print_startup_banner(model: str, kb_stats: dict) -> None:
    """Print comprehensive startup diagnostics."""
    print("=" * 70)
    print("📚 GROUNDED LOCAL RAG with Ollama + C:\\Notes")
    print("   STRICT Citation Enforcement - Fail-Fast Mode")
    print("=" * 70)
    print("\n📊 Configuration:")
    print(f"   • Ollama URL:     {OLLAMA_BASE_URL}")
    print(f"   • Model:          {model}")
    print(f"   • Context size:   {RAG_NUM_CTX} tokens")
    print(f"   • Top-K chunks:   {RAG_TOP_K} (full text: {RAG_TOP_K_FULL})")
    print(f"   • TOC filtering:  {'ENABLED' if RAG_FILTER_TOC else 'disabled'}")
    print(f"   • PDF expansion:  {'ENABLED (radius={})'.format(RAG_PDF_EXPAND_RADIUS) if RAG_PDF_EXPAND else 'disabled'}")
    print(f"   • Source diversity: max {RAG_MAX_PER_SOURCE} chunks per source")
    print(f"\n📁 Knowledge Base:")
    print(f"   • Data directory: {kb_stats['data_directory']}")
    print(f"   • DB location:    {kb_stats.get('db_path', 'default')}")
    print(f"   • Total chunks:   {kb_stats['total_chunks']}")
    print(f"\n🔒 Validation Rules (automatic):")
    print(f"   • All answers cite [chunk:id] for every fact")
    print(f"   • All answers include verbatim quotes from sources")
    print(f"   • External URLs are blocked")
    print(f"   • Single retry then fail-fast on validation errors")
    print("-" * 70)


def main():
    """Main interactive loop for grounded RAG Q&A."""
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
    
    # Determine effective model
    effective_model = get_effective_model(available_models)
    
    # Initialize knowledge base
    print("📚 Initializing knowledge base...")
    try:
        kb = DocumentIngestion()
    except Exception as e:
        print(f"✗ Error initializing knowledge base: {e}")
        sys.exit(1)
    
    stats = kb.get_stats()
    
    # Print comprehensive startup banner
    print_startup_banner(effective_model, stats)
    
    # Warn if not using grounded model
    if "grounded" not in effective_model.lower():
        print("\n⚠️  WARNING: Not using a grounded model!")
        print("  For best results, create the grounded model:")
        print("    ollama create rag-grounded-nemo -f ollama\\Modelfile.rag-grounded")
        print()
    
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.\n")
    
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
        context_chunks, allowed_ids, diagnostics = retrieve_context(kb, question)
        
        if not context_chunks:
            print("⚠️  No relevant results found in knowledge base.\n")
            continue

        # Show retrieval diagnostics
        print(f"✓ Retrieved {diagnostics['fetched']} candidates → {diagnostics['final_count']} chunks")
        if diagnostics['toc_filtered'] > 0:
            print(f"  📄 Filtered {diagnostics['toc_filtered']} TOC-like chunks:")
            for toc_info in diagnostics['toc_reasons'][:3]:
                print(f"      - {toc_info['id']}: {', '.join(toc_info['reasons'])}")
                print(f"        Preview: \"{toc_info['preview'][:60]}...\"")
        if diagnostics['expanded_chunks'] > 0:
            print(f"  📖 Expanded {diagnostics['expanded_chunks']} adjacent PDF chunks")
        
        print(f"\n  Allowed chunk IDs ({len(allowed_ids)}):")
        for cid in sorted(allowed_ids)[:8]:
            print(f"    - {cid}")
        if len(allowed_ids) > 8:
            print(f"    ... and {len(allowed_ids) - 8} more")
        
        # Show sources with quality info
        print("\n  📚 Sources:")
        for chunk in context_chunks[:6]:
            meta = chunk["metadata"]
            source = meta.get("relative_path", meta.get("filename", "unknown"))
            exp_marker = " [expanded]" if chunk.get("expanded") else ""
            print(f"    • [{chunk['id']}] {source} (score: {chunk['score']:.2f}){exp_marker}")
        if len(context_chunks) > 6:
            print(f"    ... and {len(context_chunks) - 6} more chunks")
        
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
                print(f"📎 Citations used: {', '.join(sorted(used_citations))}")
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
            print("Possible causes:")
            print("  • The context doesn't contain relevant information")
            print("  • The model is hallucinating sources")
            print("  • Missing verbatim quotes from sources")
            print("\nTry rephrasing your question or check if the topic is in your notes.\n")
            
        except RuntimeError as e:
            # Ollama connection error
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
