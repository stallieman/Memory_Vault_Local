"""
Ingestion Pipeline voor Local Knowledge Base
Verantwoordelijk voor het inlezen, chunken en indexeren van documenten.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional
import chromadb  # type: ignore
from chromadb.config import Settings  # type: ignore
from chromadb.utils import embedding_functions  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
from pypdf import PdfReader  # type: ignore


# Mapping: top-level folder (lowercase) -> source_group
SOURCE_GROUP_MAP = {
    "sql": "sql",
    "tdv": "tdv",
    "elastic": "elastic",
    "python": "python",
    "docker": "docker",
    "git": "git",
    "ai": "ai",
    "ebooks": "ebooks",
    "microsoft": "microsoft",
    "tools": "tools",
    "personal": "personal",
    "misc": "misc",
    "readwise": "misc",  # Readwise maps to misc
    "inbox": "inbox",
}


class DocumentIngestion:
    """Handles document ingestion into ChromaDB."""
    
    def __init__(self, data_dir: str = None, db_path: str = "./chroma_db"):
        # Default data dir -> C:\Notes
        if data_dir is None:
            data_dir = r"C:\Notes"
        
        self.data_dir = Path(data_dir).resolve()
        
        # DB-path remains in home (~/.local-mcp-kb/chroma_db) as before
        if db_path == "./chroma_db":
            self.db_path = Path.home() / ".local-mcp-kb" / "chroma_db"
        else:
            self.db_path = Path(db_path).resolve()
        
        # Make sure the directory exists and is writable
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Use Chroma's built-in SentenceTransformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
        )
        
        # Get or create collection with embedding function
        # If collection exists with different embedding function, delete and recreate
        try:
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "Local knowledge base documents"},
                embedding_function=self.embedding_function
            )
        except ValueError as e:
            if "embedding function conflict" in str(e).lower():
                print("⚠ Resetting collection to use new embedding function...")
                self.client.delete_collection("knowledge_base")
                self.collection = self.client.create_collection(
                    name="knowledge_base",
                    metadata={"description": "Local knowledge base documents"},
                    embedding_function=self.embedding_function
                )
            else:
                raise
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        print(f"✓ DocumentIngestion initialized")
        print(f"  - Data directory: {self.data_dir}")
        print(f"  - Database path: {self.db_path}")
        print(f"  - Current documents: {self.collection.count()}")
    
    def _doc_key(self, file_path: Path) -> str:
        """Generate a document key from file path relative to data directory."""
        try:
            rel = str(file_path.relative_to(self.data_dir))
        except ValueError:
            rel = str(file_path)
        return rel

    def _get_source_group(self, relative_path: Path) -> str:
        """
        Determine source_group from the top-level folder of relative_path.
        Returns the mapped group or 'misc' for unknown/root files.
        """
        parts = Path(relative_path).parts
        if not parts:
            return "misc"  # Root file without folder
        
        top_folder = parts[0].lower()
        return SOURCE_GROUP_MAP.get(top_folder, "misc")

    def _chunk_id(self, doc_key: str, chunk_index: int) -> str:
        """Generate a unique chunk ID from document key and chunk index."""
        h = hashlib.sha1(doc_key.encode("utf-8")).hexdigest()[:12]
        return f"{h}_{chunk_index:04d}"
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """Read file content based on extension."""
        try:
            if file_path.suffix in ['.md', '.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.suffix == '.pdf':
                # Read PDF using pypdf
                try:
                    reader = PdfReader(str(file_path))
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                    if text.strip():
                        print(f"  ✓ Extracted {len(reader.pages)} pages from PDF")
                        return text
                    else:
                        print(f"  ⚠ No text found in PDF")
                        return None
                except Exception as pdf_error:
                    print(f"  ✗ Error reading PDF: {pdf_error}")
                    return None
            else:
                print(f"⚠ Unsupported file type: {file_path.suffix}")
                return None
        except Exception as e:
            print(f"✗ Error reading {file_path.name}: {e}")
            return None
    
    def extract_heading_context(self, text: str, chunk_start: int) -> Dict[str, str]:
        """Extract heading context (h1, h2, h3) for a chunk position in markdown text."""
        headings = {"h1": "", "h2": "", "h3": "", "title": ""}
        
        # Find all markdown headings before the chunk position
        heading_pattern = r'^(#{1,3})\s+(.+)$'
        current_h1 = current_h2 = current_h3 = ""
        
        for match in re.finditer(heading_pattern, text[:chunk_start], re.MULTILINE):
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            
            if level == 1:
                current_h1 = heading_text
                current_h2 = current_h3 = ""  # Reset sub-headings
                if not headings["title"]:  # Use first h1 as title
                    headings["title"] = heading_text
            elif level == 2:
                current_h2 = heading_text
                current_h3 = ""  # Reset sub-heading
            elif level == 3:
                current_h3 = heading_text
        
        headings["h1"] = current_h1
        headings["h2"] = current_h2
        headings["h3"] = current_h3
        
        return headings
    
    def create_chunks(self, text: str, file_path: Path) -> List[Dict]:
        """Split text into chunks with enhanced metadata."""
        chunks = self.text_splitter.split_text(text)
        
        # Calculate relative path and doc_id
        try:
            relative_path = file_path.relative_to(self.data_dir)
        except ValueError:
            relative_path = file_path
        
        # Generate stable doc_id from relative path
        doc_id = hashlib.sha1(str(relative_path).encode()).hexdigest()[:12]
        
        # Detect if file is markdown for heading extraction
        is_markdown = file_path.suffix.lower() in ['.md', '.markdown']
        
        chunk_dicts = []
        char_offset = 0
        
        for i, chunk in enumerate(chunks):
            # Find chunk position in original text for heading context
            chunk_start = text.find(chunk, char_offset)
            if chunk_start == -1:
                chunk_start = char_offset
            
            # Extract heading context for markdown files
            heading_context = {}
            if is_markdown:
                heading_context = self.extract_heading_context(text, chunk_start)
            
            # Determine source_group from top-level folder
            source_group = self._get_source_group(relative_path)
            
            metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "relative_path": str(relative_path),
                "source_group": source_group,
                "file_type": file_path.suffix,
                "doc_id": doc_id,
                "chunk_id": i,
                "total_chunks": len(chunks),
                "start_char": chunk_start,
                "end_char": chunk_start + len(chunk),
            }
            
            # Add heading context if available
            if heading_context:
                metadata.update({
                    "title": heading_context.get("title", ""),
                    "h1": heading_context.get("h1", ""),
                    "h2": heading_context.get("h2", ""),
                    "h3": heading_context.get("h3", ""),
                })
            
            chunk_dicts.append({
                "text": chunk,
                "metadata": metadata
            })
            
            # Update offset for next chunk
            char_offset = chunk_start + len(chunk)
        
        return chunk_dicts
    
    def ingest_file(self, file_path: Path) -> bool:
        """Ingest a single file into the database."""
        # Calculate relative path and source_group for logging
        try:
            relative_path = file_path.relative_to(self.data_dir)
        except ValueError:
            relative_path = file_path
        source_group = self._get_source_group(relative_path)
        
        print(f"📄 Ingesting: {file_path.name}")
        print(f"   → relative_path: {relative_path}, source_group: {source_group}")
        
        # Read file
        content = self.read_file(file_path)
        if not content:
            return False
        
        # Create chunks
        chunks = self.create_chunks(content, file_path)
        if not chunks:
            print(f"⚠ No chunks created for {file_path.name}")
            return False
        
        # First, remove any existing chunks for this file
        self.remove_file(file_path)
        
        # Generate unique file identifier from relative path
        try:
            relative_path = file_path.relative_to(self.data_dir)
        except ValueError:
            relative_path = file_path
        file_hash = hashlib.sha1(str(relative_path).encode()).hexdigest()[:12]
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Use hash of relative path + chunk index for unique IDs
            chunk_id = f"{file_hash}_{chunk['metadata']['chunk_id']}"
            ids.append(chunk_id)
            documents.append(chunk['text'])
            metadatas.append(chunk['metadata'])
        
        # Add to ChromaDB (it will handle embeddings automatically)
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✓ Ingested {len(chunks)} chunks from {file_path.name}")
            return True
        except Exception as e:
            print(f"✗ Error ingesting {file_path.name}: {e}")
            return False
    
    def remove_file(self, file_path: Path) -> int:
        """
        Remove all chunks of a file from the database.
        Uses relative_path metadata for precise matching (handles same filename in different dirs).
        Returns: number of chunks removed (0 if none found or error)
        """
        try:
            # Calculate relative path to match what's stored in metadata
            try:
                relative_path = file_path.relative_to(self.data_dir)
            except ValueError:
                relative_path = file_path
            
            rel_path_str = str(relative_path)
            
            # Filter on relative_path to handle files with same name in different directories
            results = self.collection.get(
                where={"relative_path": rel_path_str}
            )
            
            if results['ids']:
                chunk_count = len(results['ids'])
                self.collection.delete(ids=results['ids'])
                print(f"🗑️  Removed {chunk_count} chunks for relative_path='{rel_path_str}'")
                return chunk_count
            return 0
        except Exception as e:
            print(f"✗ Error removing file (relative_path='{file_path}'): {e}")
            return 0
    
    def ingest_directory(self, directory: Optional[Path] = None) -> int:
        """Ingest all supported files in a directory and its subdirectories."""
        if directory is None:
            directory = self.data_dir
        
        if not directory.exists():
            print(f"✗ Directory does not exist: {directory}")
            return 0
        
        supported_extensions = {'.md', '.txt', '.pdf'}
        # Recursively find all supported files
        files = []
        for ext in supported_extensions:
            files.extend(directory.rglob(f"*{ext}"))
        
        # Sort files to process PDFs, markdown, then text files
        files = sorted(files, key=lambda f: (f.suffix != '.pdf', f.suffix != '.md', str(f)))
        
        # Count by type for reporting
        file_types = {}
        for f in files:
            file_types[f.suffix] = file_types.get(f.suffix, 0) + 1
        
        print(f"\n📚 Starting batch ingestion of {len(files)} files (including subdirectories)...")
        print(f"   File breakdown: {', '.join(f'{count} {ext} files' for ext, count in sorted(file_types.items()))}")
        
        success_count = 0
        failed_files = []
        for file_path in files:
            try:
                if self.ingest_file(file_path):
                    success_count += 1
                else:
                    failed_files.append((str(file_path), "Ingestion returned False"))
            except Exception as e:
                failed_files.append((str(file_path), str(e)))
                print(f"✗ Exception ingesting {file_path.name}: {e}")
        
        print(f"\n✓ Batch ingestion complete: {success_count}/{len(files)} files")
        if failed_files:
            print(f"⚠ Failed to ingest {len(failed_files)} files:")
            for fpath, reason in failed_files[:5]:  # Show first 5 failures
                print(f"   - {Path(fpath).name}: {reason}")
        print(f"  Total documents in database: {self.collection.count()}")
        return success_count
    
    def query(self, query_text: str, n_results: int = 5, where: Dict = None) -> Dict:
        """
        Query the knowledge base.
        
        Args:
            query_text: The search query
            n_results: Maximum number of results to return
            where: Optional filter dict, e.g. {"source_group": "sql"}
        
        Returns:
            Dict with 'results' (ChromaDB format) and 'count'
        """
        try:
            query_kwargs = {
                "query_texts": [query_text],
                "n_results": n_results,
            }
            if where:
                query_kwargs["where"] = where
            
            results = self.collection.query(**query_kwargs)
            
            return {
                "results": results,
                "count": len(results['ids'][0]) if results['ids'] else 0
            }
        except Exception as e:
            print(f"✗ Error querying: {e}")
            return {"results": None, "count": 0}
    
    def get_chunks_by_ids(self, chunk_ids: List[str]) -> Dict[str, Dict]:
        """
        Retrieve multiple chunks by their IDs.
        Returns a dict mapping chunk_id -> {"text": ..., "metadata": ...}
        """
        if not chunk_ids:
            return {}
        try:
            res = self.collection.get(
                ids=chunk_ids,
                include=["documents", "metadatas"]
            )
            result = {}
            for i, cid in enumerate(res.get("ids", [])):
                result[cid] = {
                    "text": (res.get("documents") or [])[i] if res.get("documents") else "",
                    "metadata": (res.get("metadatas") or [])[i] if res.get("metadatas") else {}
                }
            return result
        except Exception as e:
            print(f"✗ Error getting chunks by ids: {e}")
            return {}
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection.name,
            "data_directory": str(self.data_dir),
            "db_path": str(self.db_path)
        }


    def sanity_check(self, sample_size: int = 5) -> None:
        """
        Print random samples from the database to verify metadata correctness.
        Shows filename, relative_path, and source_group.
        Also shows distribution of source_groups.
        """
        import random
        from collections import Counter
        
        print(f"\n🔬 SANITY CHECK: {sample_size} random documents")
        print("=" * 60)
        
        # Get all unique relative_paths
        try:
            all_docs = self.collection.get(include=["metadatas"])
            if not all_docs['ids']:
                print("  No documents in database!")
                return
            
            # Group by relative_path to get unique docs
            unique_docs = {}
            source_group_counts = Counter()
            for i, meta in enumerate(all_docs['metadatas']):
                rel_path = meta.get('relative_path', 'unknown')
                sg = meta.get('source_group', 'unknown')
                source_group_counts[sg] += 1
                if rel_path not in unique_docs:
                    unique_docs[rel_path] = meta
            
            # Sample random docs
            sample_paths = random.sample(list(unique_docs.keys()), min(sample_size, len(unique_docs)))
            
            for i, rel_path in enumerate(sample_paths, 1):
                meta = unique_docs[rel_path]
                print(f"\n  [{i}] {meta.get('filename', 'N/A')}")
                print(f"      relative_path: {rel_path}")
                print(f"      source_group:  {meta.get('source_group', '(not set)')}")
                print(f"      total_chunks:  {meta.get('total_chunks', 'N/A')}")
            
            print(f"\n  Total unique documents: {len(unique_docs)}")
            print(f"\n  📊 SOURCE_GROUP DISTRIBUTION (chunks):")
            for sg, count in sorted(source_group_counts.items(), key=lambda x: -x[1]):
                print(f"      {sg:12}: {count:5} chunks")
            print("=" * 60)
            
        except Exception as e:
            print(f"  Error during sanity check: {e}")


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    force_reindex = "--force" in sys.argv or "-f" in sys.argv
    
    print("="*70)
    print("📚 KNOWLEDGE BASE RE-INGESTION")
    print("="*70)
    
    # Initialize ingestion
    ingestion = DocumentIngestion()
    
    # Show pre-ingest stats
    pre_count = ingestion.collection.count()
    print(f"\n📊 PRE-INGEST: {pre_count} chunks in database")
    
    if force_reindex or pre_count == 0:
        # Full re-ingest
        print("\n🔄 Starting full re-ingestion...")
        ingestion.ingest_directory()
    else:
        print(f"\n⚠ Database already has {pre_count} chunks.")
        print("  Use --force or -f to force full re-ingestion.")
        print("  Running re-ingest anyway...")
        ingestion.ingest_directory()
    
    # Show post-ingest stats
    print("\n" + "="*70)
    print("📊 POST-INGEST STATISTICS")
    print("="*70)
    stats = ingestion.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Sanity check
    ingestion.sanity_check(sample_size=5)
    
    # Test query
    print("\n🔍 Test query: 'Docker commands'")
    results = ingestion.query("Docker commands", n_results=3)
    print(f"  Found {results['count']} results")
