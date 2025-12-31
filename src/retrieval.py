"""
Relevance-Aware Prioritized Retrieval for Local Knowledge Base

Uses a preflight query + bias scoring approach:
1. Fetch top_k_total * PREFLIGHT_MULTIPLIER chunks (unfiltered)
2. Apply priority bias: adjusted_score = distance - group_bonus
3. Sort by adjusted_score, apply max_per_source constraint
4. Return top_k_total most relevant chunks

This ensures:
- TDV queries get TDV results (not forced SQL/elastic)
- SQL queries get SQL results
- Relevance always trumps group priority
"""

import os
from typing import List, Dict, Set
from collections import Counter
from ingestion import DocumentIngestion


# ============================================================================
# Configuration via environment variables
# ============================================================================
RAG_TOP_K_TOTAL = int(os.environ.get("RAG_TOP_K_TOTAL", "12"))
RAG_TOP_K_PER_GROUP = int(os.environ.get("RAG_TOP_K_PER_GROUP", "3"))  # kept for API compat
RAG_MAX_PER_SOURCE = int(os.environ.get("RAG_MAX_PER_SOURCE", "3"))  # max chunks per file
RAG_PREFLIGHT_MULT = int(os.environ.get("RAG_PREFLIGHT_MULT", "5"))  # fetch 5x candidates

# Priority bonus per group (subtracted from distance - lower = better)
# Higher bonus = more likely to be selected when relevance is similar
# Specialized domains get higher bonus to compete with large ebook corpus
GROUP_PRIORITY_BONUS = {
    "sql":       0.15,  # Strong bias for local SQL docs
    "tdv":       0.15,  # Strong bias for TDV docs
    "elastic":   0.15,  # Strong bias for Elastic docs
    "python":    0.10,
    "docker":    0.10,
    "git":       0.08,
    "ai":        0.08,
    "microsoft": 0.06,
    "tools":     0.05,
    "personal":  0.04,
    "ebooks":    0.00,  # No bonus - must win on pure relevance
    "misc":      0.00,
}

# Distance threshold: ignore chunks with distance > this (bad matches)
RAG_DISTANCE_THRESHOLD = float(os.environ.get("RAG_DISTANCE_THRESHOLD", "1.5"))

# Default priority order (for logging/reference)
DEFAULT_GROUP_ORDER = [
    "sql", "tdv", "elastic", "python", "docker", "git", 
    "ai", "microsoft", "tools", "personal", "ebooks", "misc"
]
_env_order = os.environ.get("RAG_GROUP_ORDER", "")
GROUP_ORDER = _env_order.split(",") if _env_order else DEFAULT_GROUP_ORDER


class PrioritizedRetriever:
    """
    Relevance-aware retrieval with source_group bias scoring.
    Uses preflight query + adjusted scoring instead of per-group queries.
    """
    
    def __init__(self, ingestion: DocumentIngestion = None):
        """
        Initialize retriever with an existing DocumentIngestion instance.
        If none provided, creates a new one with default settings.
        """
        self.ingestion = ingestion or DocumentIngestion()
    
    def query_with_priority(
        self,
        query_text: str,
        top_k_total: int = None,
        per_group_k: int = None,  # kept for API compat, not used in new algo
        group_order: List[str] = None,  # kept for API compat
        source_group_filter: str = None,
        max_per_source: int = None,
        verbose: bool = False,
    ) -> Dict:
        """
        Relevance-aware prioritized retrieval.
        
        Algorithm:
        1. Preflight: fetch top_k_total * PREFLIGHT_MULT candidates
        2. Filter: remove chunks above distance threshold
        3. Score: adjusted_distance = distance - group_bonus
        4. Sort: by adjusted_distance (lower = better)
        5. Constrain: max_per_source chunks per file
        6. Return: top_k_total results
        
        Args:
            query_text: The search query
            top_k_total: Maximum total chunks to return (default: RAG_TOP_K_TOTAL)
            per_group_k: Ignored (kept for API compatibility)
            group_order: Ignored (kept for API compatibility)
            source_group_filter: If set, only query this specific group
            max_per_source: Max chunks from same file (default: RAG_MAX_PER_SOURCE)
            verbose: Log detailed scoring info
        
        Returns:
            Dict with keys:
                - results: ChromaDB-style results dict
                - count: Number of results
                - group_stats: Dict mapping source_group -> chunk count
                - scoring_log: List of scoring details (if verbose)
        """
        top_k_total = top_k_total or RAG_TOP_K_TOTAL
        max_per_source = max_per_source or RAG_MAX_PER_SOURCE
        
        # If filtering to a specific group, do a simple filtered query
        if source_group_filter:
            return self._query_single_group(query_text, source_group_filter, top_k_total)
        
        # STEP 1: Preflight query - fetch many candidates
        preflight_n = top_k_total * RAG_PREFLIGHT_MULT
        preflight_results = self.ingestion.query(
            query_text=query_text,
            n_results=preflight_n,
            where=None  # Unfiltered
        )
        
        if not preflight_results.get("results") or not preflight_results["results"].get("ids"):
            return self._empty_result()
        
        results = preflight_results["results"]
        candidates = []
        
        # STEP 2: Build candidate list with scoring
        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 0.0
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            document = results["documents"][0][i] if results.get("documents") else ""
            
            # Filter out bad matches
            if distance > RAG_DISTANCE_THRESHOLD:
                continue
            
            source_group = metadata.get("source_group", "misc")
            filename = metadata.get("filename", "unknown")
            
            # STEP 3: Calculate adjusted score with group bonus
            group_bonus = GROUP_PRIORITY_BONUS.get(source_group, 0.0)
            adjusted_distance = distance - group_bonus
            
            candidates.append({
                "id": chunk_id,
                "document": document,
                "metadata": metadata,
                "distance": distance,
                "adjusted_distance": adjusted_distance,
                "source_group": source_group,
                "filename": filename,
                "group_bonus": group_bonus,
            })
        
        # STEP 4: Sort by adjusted distance (lower = better)
        candidates.sort(key=lambda x: x["adjusted_distance"])
        
        # STEP 5: Apply max_per_source constraint
        selected = []
        source_counts: Dict[str, int] = Counter()
        scoring_log = []
        
        for cand in candidates:
            if len(selected) >= top_k_total:
                break
            
            filename = cand["filename"]
            if source_counts[filename] >= max_per_source:
                continue
            
            source_counts[filename] += 1
            selected.append(cand)
            
            if verbose:
                scoring_log.append({
                    "rank": len(selected),
                    "filename": filename,
                    "source_group": cand["source_group"],
                    "distance": round(cand["distance"], 4),
                    "bonus": cand["group_bonus"],
                    "adjusted": round(cand["adjusted_distance"], 4),
                })
        
        # Build group stats
        group_stats = Counter(c["source_group"] for c in selected)
        
        # Convert to ChromaDB format
        result = self._to_chroma_format(selected, dict(group_stats))
        
        if verbose:
            result["scoring_log"] = scoring_log
        
        return result
    
    def _query_single_group(self, query_text: str, group: str, n_results: int) -> Dict:
        """Query a single source_group with filter."""
        results = self.ingestion.query(
            query_text=query_text,
            n_results=n_results,
            where={"source_group": group}
        )
        
        group_stats = {group: results.get("count", 0)}
        return {
            "results": results.get("results"),
            "count": results.get("count", 0),
            "group_stats": group_stats,
        }
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            "results": {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]},
            "count": 0,
            "group_stats": {},
        }
    
    def _to_chroma_format(self, chunks: List[Dict], group_stats: Dict[str, int]) -> Dict:
        """Convert chunk list to ChromaDB-compatible results format."""
        if not chunks:
            return self._empty_result()
        
        return {
            "results": {
                "ids": [[c["id"] for c in chunks]],
                "documents": [[c["document"] for c in chunks]],
                "metadatas": [[c["metadata"] for c in chunks]],
                "distances": [[c["distance"] for c in chunks]],  # Original distance
            },
            "count": len(chunks),
            "group_stats": group_stats,
        }


def prioritized_query(
    query_text: str,
    ingestion: DocumentIngestion = None,
    top_k_total: int = None,
    max_per_source: int = None,
    source_group_filter: str = None,
    verbose: bool = False,
) -> Dict:
    """
    Convenience function for relevance-aware prioritized retrieval.
    
    Args:
        query_text: The search query
        ingestion: Optional DocumentIngestion instance (creates new if None)
        top_k_total: Maximum total chunks to return
        max_per_source: Max chunks from same file
        source_group_filter: If set, only query this specific group
        verbose: Include detailed scoring log
    
    Returns:
        Dict with results, count, group_stats, and optionally scoring_log
    """
    retriever = PrioritizedRetriever(ingestion)
    return retriever.query_with_priority(
        query_text=query_text,
        top_k_total=top_k_total,
        max_per_source=max_per_source,
        source_group_filter=source_group_filter,
        verbose=verbose,
    )


# ============================================================================
# Test / Sanity Check with verbose scoring
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("RELEVANCE-AWARE PRIORITIZED RETRIEVAL TEST")
    print("=" * 80)
    print(f"Config: TOP_K={RAG_TOP_K_TOTAL}, MAX_PER_SOURCE={RAG_MAX_PER_SOURCE}, "
          f"PREFLIGHT_MULT={RAG_PREFLIGHT_MULT}, THRESHOLD={RAG_DISTANCE_THRESHOLD}")
    print(f"Group bonuses: {GROUP_PRIORITY_BONUS}")
    
    # Test queries - each should favor its domain
    test_queries = [
        ("CTE join SQL query", "sql"),
        ("TDV caching performance tuning", "tdv"),
        ("ILM policy Elasticsearch lifecycle", "elastic"),
    ]
    
    retriever = PrioritizedRetriever()
    
    for query, expected_group in test_queries:
        print(f"\n{'='*80}")
        print(f"🔍 Query: '{query}'")
        print(f"   Expected dominant group: {expected_group}")
        print("-" * 80)
        
        result = retriever.query_with_priority(query, verbose=True)
        
        print(f"\n📊 Results: {result['count']} chunks")
        print(f"   Group distribution: {dict(result['group_stats'])}")
        
        # Check if expected group dominates
        if result['group_stats']:
            top_group = max(result['group_stats'], key=result['group_stats'].get)
            top_count = result['group_stats'][top_group]
            expected_count = result['group_stats'].get(expected_group, 0)
            
            if expected_group == top_group or expected_count >= top_count:
                print(f"   ✅ {expected_group} dominates or ties ({expected_count} chunks)")
            else:
                print(f"   ⚠️  {top_group} dominates ({top_count}), expected {expected_group} ({expected_count})")
        
        # Show scoring details
        if result.get("scoring_log"):
            print(f"\n   Scoring log (top 6):")
            print(f"   {'Rank':<5} {'File':<40} {'Group':<10} {'Dist':<8} {'Bonus':<7} {'Adj':<8}")
            print(f"   {'-'*5} {'-'*40} {'-'*10} {'-'*8} {'-'*7} {'-'*8}")
            for entry in result["scoring_log"][:6]:
                fname = entry["filename"][:38] + ".." if len(entry["filename"]) > 40 else entry["filename"]
                print(f"   {entry['rank']:<5} {fname:<40} {entry['source_group']:<10} "
                      f"{entry['distance']:<8.4f} {entry['bonus']:<7.2f} {entry['adjusted']:<8.4f}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print("=" * 80)
