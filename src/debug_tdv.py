"""Debug script to analyze TDV caching chunks."""
from ingestion import DocumentIngestion

kb = DocumentIngestion()

# Query 1: Generic caching
print("=" * 70)
print("QUERY 1: 'caching pitfalls data virtualization'")
print("=" * 70)
result = kb.query("caching pitfalls data virtualization", n_results=10)
for i in range(len(result['results']['ids'][0])):
    cid = result['results']['ids'][0][i]
    meta = result['results']['metadatas'][0][i]
    dist = result['results']['distances'][0][i]
    doc = result['results']['documents'][0][i]
    source = meta.get('relative_path', meta.get('filename', '?'))
    score = 1 - dist
    is_tdv = 'tdv' in source.lower() or 'tibco' in source.lower()
    marker = "🎯 TDV" if is_tdv else "   "
    print(f"{marker} {i+1}. [{cid}] score={score:.3f}")
    print(f"       Source: {source}")
    print(f"       Preview: {doc[:100].replace(chr(10), ' ')}...")
    print()

# Query 2: Specific TDV
print("=" * 70)
print("QUERY 2: 'TDV TIBCO cache invalidation refresh incremental'")
print("=" * 70)
result2 = kb.query("TDV TIBCO cache invalidation refresh incremental", n_results=10)
for i in range(len(result2['results']['ids'][0])):
    cid = result2['results']['ids'][0][i]
    meta = result2['results']['metadatas'][0][i]
    dist = result2['results']['distances'][0][i]
    doc = result2['results']['documents'][0][i]
    source = meta.get('relative_path', meta.get('filename', '?'))
    score = 1 - dist
    is_tdv = 'tdv' in source.lower() or 'tibco' in source.lower()
    marker = "🎯 TDV" if is_tdv else "   "
    print(f"{marker} {i+1}. [{cid}] score={score:.3f}")
    print(f"       Source: {source}")
    print(f"       Preview: {doc[:100].replace(chr(10), ' ')}...")
    print()

# Count TDV chunks total
print("=" * 70)
print("TDV CHUNKS IN DATABASE:")
print("=" * 70)
# This is a rough estimate - check filenames
all_results = kb.query("TIBCO TDV data virtualization", n_results=100)
tdv_count = sum(1 for m in all_results['results']['metadatas'][0] 
                if 'tdv' in m.get('relative_path', '').lower())
print(f"Found ~{tdv_count} TDV-related chunks in top 100 results")
