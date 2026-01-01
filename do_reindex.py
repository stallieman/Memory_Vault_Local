"""Quick reindex script - deletes and rebuilds the entire knowledge base."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ingestion import DocumentIngestion  # type: ignore

print("=" * 70)
print("FULL RE-INDEX - Starting...")
print("=" * 70)

# Initialize
print("\n1. Initializing DocumentIngestion...")
ing = DocumentIngestion()

# Get current stats
stats_before = ing.get_stats()
print(f"   Current chunks: {stats_before['total_chunks']}")
print(f"   Data directory: {stats_before['data_directory']}")
print(f"   DB path: {stats_before['db_path']}")

# Delete collection
print("\n2. Deleting existing collection...")
try:
    ing.client.delete_collection('knowledge_base')
    print("   ✓ Collection deleted")
except Exception as e:
    print(f"   Note: {e}")

# Recreate collection
print("\n3. Creating fresh collection...")
ing.collection = ing.client.get_or_create_collection(
    name='knowledge_base',
    metadata={'description': 'Local knowledge base documents'},
    embedding_function=ing.embedding_function
)
print("   ✓ Collection created")

# Ingest all files
print("\n4. Ingesting all files from C:\\Notes...")
print("   (This will take several minutes for ~35k chunks)")
ing.ingest_directory()

# Final stats
stats_after = ing.get_stats()
print("\n" + "=" * 70)
print("RE-INDEX COMPLETE!")
print("=" * 70)
print(f"Total chunks indexed: {stats_after['total_chunks']}")
print(f"Data directory: {stats_after['data_directory']}")
print("=" * 70)
