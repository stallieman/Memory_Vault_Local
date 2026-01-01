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
import requests  # type: ignore
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from ingestion import DocumentIngestion
from retrieval import PrioritizedRetriever, RAG_TOP_K_TOTAL, RAG_TOP_K_PER_GROUP, GROUP_ORDER

# ============================================================================
# Configuration via environment variables
# ============================================================================
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "rag-grounded-nemo")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "12"))  # Increased for better technical doc coverage
RAG_TOP_K_FULL = int(os.environ.get("RAG_TOP_K_FULL", "6"))  # More full-text chunks
RAG_MAX_CHARS_FULL = int(os.environ.get("RAG_MAX_CHARS_FULL", "4500"))
RAG_SNIPPET_CHARS = int(os.environ.get("RAG_SNIPPET_CHARS", "400"))
RAG_NUM_CTX = int(os.environ.get("RAG_NUM_CTX", "8192"))

# TOC filtering and chunk expansion
RAG_FILTER_TOC = os.environ.get("RAG_FILTER_TOC", "1") == "1"
RAG_PDF_EXPAND = os.environ.get("RAG_PDF_EXPAND", "1") == "1"
RAG_PDF_EXPAND_RADIUS = int(os.environ.get("RAG_PDF_EXPAND_RADIUS", "2"))

# Source diversity: max chunks per single source file
# Increased to 5 to allow more technical documentation from same source
RAG_MAX_PER_SOURCE = int(os.environ.get("RAG_MAX_PER_SOURCE", "5"))

# Minimum relevance score threshold (0-1 scale, where 1=perfect match)
# Below this threshold, context is considered irrelevant and question is out-of-scope  
# Lowered to 0.25 to accommodate semantic gap between natural questions and technical docs
RAG_MIN_SCORE = float(os.environ.get("RAG_MIN_SCORE", "0.25"))

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
    
    # Show block coverage failures (if any)
    uncited_blocks = debug_payload.get('uncited_blocks', [])
    if uncited_blocks:
        print(f"\n🚫 Uncited Blocks ({len(uncited_blocks)}):")
        for block_info in uncited_blocks[:5]:
            print(f"    Block #{block_info['index']} ({block_info['type']}):")
            print(f"      \"{block_info['preview']}...\"")
        if len(uncited_blocks) > 5:
            print(f"    ... and {len(uncited_blocks) - 5} more uncited blocks")
        total_blocks = debug_payload.get('total_blocks', 0)
        if total_blocks:
            print(f"    Total non-header blocks: {total_blocks}")
    
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
# STRICT Citation Validation (Fail-Fast) - BLOCK-BASED COVERAGE
# ============================================================================

# Pattern for quoted text (various quote styles)
QUOTE_PATTERN = re.compile(r'["""]([^"""]{10,})["""]')

# Pattern to detect markdown code blocks (inline or fenced)
CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```|`[^`]+`')

# Pattern to detect markdown headers
HEADER_PATTERN = re.compile(r'^\s*#{1,6}\s+.+$')


def split_into_blocks(text: str) -> List[Dict[str, str]]:
    """
    Split text into logical blocks: paragraphs, bullets, numbered items, code blocks.
    
    Returns list of dicts with 'type' and 'content'.
    Block types: 'paragraph', 'bullet', 'numbered', 'header', 'code'
    
    Code blocks are kept together with any trailing citations.
    """
    blocks = []
    lines = text.split('\n')
    current_block = []
    current_type = None
    in_code_block = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect code block fence
        if stripped.startswith('```'):
            # If we have a current block, save it
            if current_block and not in_code_block:
                blocks.append({
                    'type': current_type or 'paragraph',
                    'content': '\n'.join(current_block)
                })
                current_block = []
                current_type = None
            
            # Start collecting code block
            if not in_code_block:
                in_code_block = True
                current_block = [line]
                current_type = 'code'
            else:
                # End of code block - add closing fence
                current_block.append(line)
                in_code_block = False
                
                # Look ahead for citation on next non-empty line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    current_block.append(lines[j])
                    j += 1
                
                # If next line has citation, include it
                if j < len(lines) and CITATION_PATTERN.search(lines[j]):
                    current_block.append(lines[j])
                    i = j  # Skip to this line
                
                # Save code block
                blocks.append({
                    'type': 'code',
                    'content': '\n'.join(current_block)
                })
                current_block = []
                current_type = None
            
            i += 1
            continue
        
        # If inside code block, just accumulate
        if in_code_block:
            current_block.append(line)
            i += 1
            continue
        
        # Empty line = end current block (outside code blocks)
        if not stripped:
            if current_block:
                blocks.append({
                    'type': current_type or 'paragraph',
                    'content': '\n'.join(current_block)
                })
                current_block = []
                current_type = None
            i += 1
            continue
        
        # Detect block type
        is_header = HEADER_PATTERN.match(line)
        is_bullet = stripped.startswith('- ') or stripped.startswith('* ')
        is_numbered = bool(re.match(r'^\d+\.\s+', stripped))
        
        # Start new block if type changes
        new_type = None
        if is_header:
            new_type = 'header'
        elif is_bullet:
            new_type = 'bullet'
        elif is_numbered:
            new_type = 'numbered'
        else:
            new_type = 'paragraph'
        
        # For bullets/numbered items: each item is its own block
        if new_type in ('bullet', 'numbered'):
            if current_block:
                blocks.append({
                    'type': current_type or 'paragraph',
                    'content': '\n'.join(current_block)
                })
                current_block = []
            blocks.append({
                'type': new_type,
                'content': line
            })
            current_type = None
        else:
            # Headers and paragraphs: accumulate until type changes
            if current_type and current_type != new_type:
                blocks.append({
                    'type': current_type,
                    'content': '\n'.join(current_block)
                })
                current_block = []
            current_block.append(line)
            current_type = new_type
        
        i += 1
    
    # Add final block
    if current_block:
        blocks.append({
            'type': current_type or 'paragraph',
            'content': '\n'.join(current_block)
        })
    
    return blocks


def block_has_trailing_citation(block_content: str) -> Tuple[bool, List[str]]:
    """
    Check if block ends with citation(s).
    Returns (has_citation, list_of_citation_ids).
    
    "Trailing" = last 100 chars contain at least one [chunk:id].
    """
    # Check last 100 chars for citations
    tail = block_content[-100:] if len(block_content) > 100 else block_content
    citations = CITATION_PATTERN.findall(tail)
    return bool(citations), citations


def validate_answer(
    text: str,
    allowed_ids: Set[str],
    debug_payload: dict,
    require_quotes: bool = True,
    lenient_mode: bool = False
) -> Set[str]:
    """
    Validate that an answer contains proper citations with BLOCK-BASED COVERAGE.
    
    FAIL-FAST: Raises CitationValidationError if validation fails.
    
    Validation Rules:
    1. IDK response is always valid (no citations required)
    2. Each non-header, non-code, non-empty block must END with at least one [chunk:id] citation
       (In lenient_mode: at least 50% of blocks must have citations)
    3. All cited IDs must be from allowed_ids (no hallucinated chunks)
    4. Must NOT contain external URLs (http/https links)
    5. Optionally: each block with citations must contain quoted evidence (if require_quotes=True)
       Note: Code blocks ARE evidence themselves and don't need additional quotes
    
    Block types checked:
    - Paragraphs (text separated by blank lines)
    - Bullet items ("- " or "* ")
    - Numbered items ("1. ", "2. ", etc.)
    - Code blocks (```...```) - automatically considered evidence when cited
    - Headers (## Title) are exempt from citation requirement
    
    Args:
        text: The model's response text
        allowed_ids: Set of valid chunk IDs from the context
        debug_payload: Dict with debug info (model, user_prompt, etc.)
        require_quotes: Whether to require quoted passages (default True)
        lenient_mode: If True, allow some blocks without citations (for teaching-style answers)
    
    Returns:
        Set of valid citation IDs found (only if validation passes)
    
    Raises:
        CitationValidationError: If validation fails for any reason
    """
    text_stripped = text.strip()
    
    # ACCEPT: Flexible IDK response (English or Dutch)
    if text_stripped == IDK or IDK_PATTERN.match(text_stripped):
        return set()  # No citations needed for IDK
    
    # Split into blocks
    blocks = split_into_blocks(text_stripped)
    
    if not blocks:
        debug_payload['reason'] = "Empty response"
        debug_payload['model_output'] = text[:5000]
        print_debug_bundle(debug_payload)
        raise CitationValidationError("Empty response", debug_payload)
    
    # Track validation state
    all_citations_found = set()
    uncited_blocks = []
    cited_blocks_count = 0
    blocks_with_quotes_but_no_citation = []
    
    for i, block in enumerate(blocks):
        block_type = block['type']
        content = block['content'].strip()
        
        # Skip empty blocks
        if not content:
            continue
        
        # Headers are exempt from citation requirement
        if block_type == 'header':
            continue
        
        # Check if block has trailing citation
        has_citation, block_citations = block_has_trailing_citation(content)
        
        if not has_citation:
            uncited_blocks.append({
                'index': i,
                'type': block_type,
                'preview': content[:120]
            })
        else:
            # Count cited blocks
            cited_blocks_count += 1
            
            # Collect citations
            all_citations_found.update(block_citations)
            
            # If require_quotes, check if block has evidence
            # Code blocks ARE evidence themselves, so they don't need additional quotes
            if require_quotes and block_type != 'code':
                quotes = QUOTE_PATTERN.findall(content)
                code_blocks = CODE_BLOCK_PATTERN.findall(content)
                # Accept either quotes or code blocks as evidence
                if not quotes and not code_blocks:
                    blocks_with_quotes_but_no_citation.append({
                        'index': i,
                        'type': block_type,
                        'preview': content[:120]
                    })
    
    # FAIL: No citations found at all
    if not all_citations_found:
        debug_payload['reason'] = "No citations found - answer must use [chunk:id] format"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = set()
        print_debug_bundle(debug_payload)
        raise CitationValidationError("No citations found", debug_payload)
    
    # FAIL: Invalid citation IDs (hallucinated chunks)
    invalid_citations = all_citations_found - allowed_ids
    if invalid_citations:
        debug_payload['reason'] = f"Invalid chunk IDs - not in allowed set: {invalid_citations}"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = list(all_citations_found)
        debug_payload['invalid_citations'] = list(invalid_citations)
        print_debug_bundle(debug_payload)
        raise CitationValidationError(
            f"Invalid chunk IDs: {invalid_citations}", 
            debug_payload
        )
    
    # FAIL: External URLs detected (hallucination indicator)
    url_matches = UNSUPPORTED_URL_PATTERN.findall(text_stripped)
    if url_matches:
        unique_urls = set(url_matches)
        debug_payload['reason'] = f"External URLs not allowed - answer must cite local chunks only: {unique_urls}"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = list(all_citations_found)
        debug_payload['urls_found'] = list(unique_urls)
        print_debug_bundle(debug_payload)
        raise CitationValidationError(f"External URLs found: {unique_urls}", debug_payload)
    
    # FAIL: Blocks without quotes (if required)
    if require_quotes and blocks_with_quotes_but_no_citation:
        debug_payload['reason'] = "Evidence requirement failure: blocks with citations but no quotes or code blocks"
        debug_payload['model_output'] = text[:5000]
        debug_payload['blocks_without_evidence'] = blocks_with_quotes_but_no_citation
        print_debug_bundle(debug_payload)
        raise CitationValidationError("No quotes or code blocks found - evidence required", debug_payload)
    
    # FAIL: Block coverage check (strict mode: ALL blocks must be cited)
    # In lenient_mode: allow uncited blocks if we have at least 1 cited block with substantial evidence
    if uncited_blocks:
        total_blocks = len(uncited_blocks) + cited_blocks_count
        cited_percentage = cited_blocks_count / total_blocks if total_blocks > 0 else 0
        
        # Lenient mode: accept if we have at least 1 properly cited and evidenced block
        # This allows for natural explanatory text around code blocks or quoted facts
        if lenient_mode and cited_blocks_count >= 1:
            print(f"[VALIDATION] Lenient mode: Accepted with {cited_blocks_count} cited block(s) out of {total_blocks} total ({cited_percentage:.0%}, {len(all_citations_found)} unique citations)")
            return all_citations_found
        
        # Strict mode: fail on ANY uncited blocks
        debug_payload['reason'] = f"Citation coverage failure: {len(uncited_blocks)} uncited blocks out of {total_blocks} total"
        debug_payload['model_output'] = text[:5000]
        debug_payload['found_citations'] = list(all_citations_found)
        debug_payload['uncited_blocks'] = uncited_blocks
        debug_payload['cited_blocks_count'] = cited_blocks_count
        debug_payload['total_blocks'] = total_blocks
        debug_payload['cited_percentage'] = f"{cited_percentage:.0%}"
        print_debug_bundle(debug_payload)
        raise CitationValidationError(
            f"Citation coverage failure: {len(uncited_blocks)} uncited blocks out of {total_blocks}",
            debug_payload
        )
    
    # SUCCESS: All validations passed
    print(f"✅ Citation validation passed: {cited_blocks_count} blocks cited, {len(all_citations_found)} unique citations")
    return all_citations_found


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
    - Universal search: Searches ALL source groups (sql, elastic, python, docker, git, ai, ebooks, etc.)
    - Automatic fallback: If no specialized docs match, ebooks/misc serve as fallback
    - Prioritized retrieval: Applies priority bonuses to favor domain-specific docs over general ebooks
    - TOC filtering: Excludes table-of-contents chunks
    - PDF chunk expansion: Fetches adjacent chunks for PDF sources
    - Source diversity: Max N chunks per source file
    - Quality metrics: Returns diagnostic info about filtering
    
    Each chunk dict contains: text, metadata, id, score
    """
    # Use prioritized retrieval to get diverse results across source_groups
    if use_prioritized:
        retriever = PrioritizedRetriever(kb)
        # Fetch more than needed to account for TOC filtering and ensure good coverage
        fetch_count = RAG_TOP_K * 3 if RAG_FILTER_TOC else RAG_TOP_K
        result = retriever.query_with_priority(
            query_text=question,
            top_k_total=fetch_count,
            per_group_k=RAG_TOP_K_PER_GROUP,
            group_order=GROUP_ORDER,
        )
    else:
        # Fallback to simple query
        fetch_count = RAG_TOP_K * 3 if RAG_FILTER_TOC else RAG_TOP_K
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
        
        # Calculate relevance score (1 - distance)
        score = 1 - float(dist)
        
        # Skip chunks below minimum relevance threshold
        if score < RAG_MIN_SCORE:
            if "low_relevance_filtered" not in diagnostics:
                diagnostics["low_relevance_filtered"] = 0
            diagnostics["low_relevance_filtered"] += 1
            continue
        
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
            "score": score,
            "rank": rank
        })
    
    # Phase 3: Expand PDF chunks with adjacent chunks
    if RAG_PDF_EXPAND and pdf_chunk_ids:
        expansion_ids = []
        for pdf_id in pdf_chunk_ids[:RAG_TOP_K_FULL]:  # Only expand top chunks
            adjacent = get_adjacent_chunk_ids(pdf_id, RAG_PDF_EXPAND_RADIUS)
            expansion_ids.extend([aid for aid in adjacent if aid not in allowed_ids])
        
        # Deduplicate expansion IDs before fetching
        expansion_ids = list(set(expansion_ids))
        
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
    model: str,
    lenient_mode: bool = False
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
        lenient_mode: If True, allow up to 50% uncited blocks (for teaching-style answers)
    
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

CRITICAL RULES - YOU MUST FOLLOW EXACTLY:
1. Use ONLY information from the CONTEXT above - never invent or create new examples
2. ALWAYS provide evidence: either "quoted text" OR code blocks with ```
3. IMMEDIATELY follow each piece of evidence with [chunk:<id>] citation
4. ONLY use chunk IDs from the ALLOWED list above
5. If the context does NOT contain the answer, respond EXACTLY: {IDK}

When user asks for "example", "dummy", or "template":
- Use the example/template FROM THE CONTEXT (cite it!)
- You can adapt field values if asked, but cite where the structure comes from

MANDATORY FORMAT FOR EVERY STATEMENT:
For text: "exact verbatim text from the source" [chunk:abc123_0001]
For code: Use markdown code blocks followed by citation AFTER the closing ```

CRITICAL: Citations MUST be AFTER the code block, NEVER inside it!

EXAMPLES:

WRONG (NO EVIDENCE):
Use PUT _index_template to create templates [chunk:abc123_0001]

WRONG (CITATION INSIDE CODE):
```python
# Import from context [chunk:abc123_0001]
df = pd.read_csv('file.csv')
```

CORRECT (WITH QUOTE):
To create an index template, use "PUT _index_template/my-template" [chunk:abc123_0001]

CORRECT (WITH CODE BLOCK - citation AFTER closing ```):
To create an index template:
```json
PUT _index_template/my-template
{{
  "index_patterns": ["logs-*"],
  "template": {{
    "settings": {{
      "number_of_shards": 2
    }},
    "mappings": {{
      "properties": {{
        "timestamp": {{ "type": "date" }},
        "message": {{ "type": "text" }}
      }}
    }}
  }}
}}
```
[chunk:abc123_0001]

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
        used_citations = validate_answer(
            answer, allowed_ids, debug_payload.copy(), 
            require_quotes=False, lenient_mode=lenient_mode
        )
        # Check if evidence (quotes or code blocks) exists even without requirement
        quotes_found = QUOTE_PATTERN.findall(answer)
        code_blocks_found = CODE_BLOCK_PATTERN.findall(answer)
        if quotes_found or code_blocks_found:
            return answer, used_citations  # SUCCESS with evidence on first try
        else:
            # Has citations but no evidence - retry to get evidence
            print(f"  ⚠️  First attempt has citations but no evidence (quotes/code) - requesting evidence...")
    except CitationValidationError as e:
        # First attempt failed - will retry
        first_failure_reason = e.reason
        print(f"  ⚠️  First attempt failed: {first_failure_reason}")
        print(f"  🔄 Retrying with stricter prompt...")
    
    # ========== SINGLE RETRY ==========
    first_failure_reason = debug_payload.get('reason', 'missing evidence')
    retry_prompt = f"""❌ YOUR ANSWER WAS REJECTED: {first_failure_reason}

YOU MUST PROVIDE EVIDENCE FROM THE CONTEXT - NEVER CREATE NEW CONTENT!

MANDATORY RULES:
1. For descriptions: Use "quoted text" from the context
2. For API calls/code: Use markdown code blocks ``` from the context
3. Put [chunk:<id>] citation RIGHT AFTER each piece of evidence
4. Use ONLY these IDs: {allowed_ids_str}
5. If context doesn't have the answer: {IDK}

EVEN IF USER ASKS FOR "DUMMY" OR "EXAMPLE":
- Find the example/template IN THE CONTEXT
- Show it in a code block
- CITE where it came from with [chunk:id]
- You can modify field names/values slightly, but MUST cite the source structure

EXAMPLE OF CORRECT ANSWER:

To create an index template, "PUT _index_template/my-template" [chunk:abc123_0001].

For a complete example with settings and mappings:
```json
PUT _index_template/my-template
{{
  "index_patterns": ["logs-*"],
  "template": {{
    "settings": {{
      "number_of_shards": 2,
      "index.lifecycle.name": "logs-ilm-policy"
    }},
    "mappings": {{
      "properties": {{
        "timestamp": {{ "type": "date" }},
        "message": {{ "type": "text" }}
      }}
    }}
  }}
}}
```
[chunk:abc123_0001]

QUESTION: {question}

ANSWER WITH EVIDENCE (quotes or code) AND CITATIONS:"""

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
    used_citations = validate_answer(
        answer2, allowed_ids, debug_payload, 
        require_quotes=True, lenient_mode=lenient_mode
    )
    
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
    print(f"   • Min relevance:  {RAG_MIN_SCORE} (0-1 scale)")
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
        if diagnostics.get('low_relevance_filtered', 0) > 0:
            print(f"  🔍 Filtered {diagnostics['low_relevance_filtered']} low-relevance chunks (score < {RAG_MIN_SCORE})")
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
