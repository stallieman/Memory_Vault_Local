"""
Final sanity check script for the reorganized knowledge base.
"""

import sys
sys.path.insert(0, "src")

from collections import Counter
from ingestion import DocumentIngestion
from retrieval import PrioritizedRetriever, GROUP_PRIORITY_BONUS

def main():
    print("=" * 80)
    print("FINAL SANITY CHECK - Relevance-Aware Retrieval")
    print("=" * 80)
    
    # Initialize
    ing = DocumentIngestion()
    
    # Get stats
    stats = ing.get_stats()
    print(f"\nTotal chunks: {stats['total_chunks']}")
    print(f"Collection: {stats['collection_name']}")
    print(f"Data dir: {stats['data_directory']}")
    print(f"DB path: {stats['db_path']}")
    
    # Get source_group distribution
    all_docs = ing.collection.get(include=["metadatas"])
    sg_counts = Counter()
    for meta in all_docs["metadatas"]:
        sg = meta.get("source_group", "unknown")
        sg_counts[sg] += 1
    
    print(f"\nSOURCE_GROUP DISTRIBUTION:")
    for sg, count in sorted(sg_counts.items(), key=lambda x: -x[1]):
        bonus = GROUP_PRIORITY_BONUS.get(sg, 0.0)
        print(f"  {sg:12}: {count:5} chunks (bonus: {bonus:.2f})")
    
    # Test 3 queries
    print("\n" + "=" * 80)
    print("TEST QUERIES (Relevance-Aware Prioritized Retrieval)")
    print("=" * 80)
    
    retriever = PrioritizedRetriever(ing)
    
    test_queries = [
        ("CTE join SQL query", "sql"),
        ("TDV caching performance", "tdv"), 
        ("ILM policy Elasticsearch lifecycle", "elastic")
    ]
    
    all_passed = True
    for q, expected in test_queries:
        result = retriever.query_with_priority(q, verbose=True)
        
        print(f"\n🔍 Query: '{q}'")
        print(f"   Expected dominant: {expected}")
        print(f"   Results: {result['count']}")
        print(f"   Groups: {dict(result['group_stats'])}")
        
        # Check dominance
        if result['group_stats']:
            top_group = max(result['group_stats'], key=result['group_stats'].get)
            expected_count = result['group_stats'].get(expected, 0)
            top_count = result['group_stats'][top_group]
            
            if expected_count >= top_count * 0.5:  # At least half of top
                print(f"   ✅ PASS - {expected}: {expected_count} chunks")
            else:
                print(f"   ⚠️  WARN - {top_group} dominates ({top_count}), expected {expected} ({expected_count})")
                all_passed = False
        
        # Show top 3 scoring entries
        if result.get("scoring_log"):
            print(f"   Top 3 adjusted scores:")
            for entry in result["scoring_log"][:3]:
                fname = entry["filename"][:30]
                print(f"      {entry['source_group']:10} {entry['adjusted']:.4f} <- {fname}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ SANITY CHECK PASSED - All queries return expected group dominance")
    else:
        print("⚠️  SANITY CHECK: Some queries may need bonus tuning")
    print("=" * 80)


if __name__ == "__main__":
    main()
