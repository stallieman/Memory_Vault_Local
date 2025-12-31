"""
Ingestion Pipeline voor Local Knowledge Base
Verantwoordelijk voor het inlezen, chunken en indexeren van documenten.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


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
            
            metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "relative_path": str(relative_path),
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
        print(f"📄 Ingesting: {file_path.name}")
        
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
    
    def remove_file(self, file_path: Path) -> bool:
        """Remove all chunks of a file from the database."""
        try:
            # Calculate relative path to match what's stored in metadata
            try:
                relative_path = file_path.relative_to(self.data_dir)
            except ValueError:
                relative_path = file_path
            
            # Filter on relative_path to handle files with same name in different directories
            results = self.collection.get(
                where={"relative_path": str(relative_path)}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"🗑️  Removed {len(results['ids'])} chunks from {file_path.name}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error removing {file_path.name}: {e}")
            return False
    
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
    
    def query(self, query_text: str, n_results: int = 5) -> Dict:
        """Query the knowledge base."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
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


if __name__ == "__main__":
    # Test ingestion
    ingestion = DocumentIngestion()
    ingestion.ingest_directory()
    
    # Test query
    print("\n🔍 Testing query...")
    results = ingestion.query("Docker commands", n_results=3)
    print(f"Found {results['count']} results")
    
    # Show stats
    print("\n📊 Database stats:")
    stats = ingestion.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
