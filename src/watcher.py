"""
File System Watcher Service
Monitort de ./data directory en triggert automatische ingestion bij wijzigingen.
"""

import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from ingestion import DocumentIngestion

# Force unbuffered output for logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


class KnowledgeBaseEventHandler(FileSystemEventHandler):
    """Handler voor file system events."""
    
    def __init__(self, ingestion: DocumentIngestion):
        super().__init__()
        self.ingestion = ingestion
        self.supported_extensions = {'.md', '.txt', '.pdf'}
    
    def _is_supported_file(self, path: str) -> bool:
        """Check if file extension is supported."""
        return Path(path).suffix in self.supported_extensions
    
    def on_created(self, event: FileSystemEvent):
        """Triggered when a new file is created."""
        if not event.is_directory and self._is_supported_file(event.src_path):
            print(f"\n🆕 New file detected: {Path(event.src_path).name}")
            self.ingestion.ingest_file(Path(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Triggered when a file is modified."""
        if not event.is_directory and self._is_supported_file(event.src_path):
            print(f"\n✏️  File modified: {Path(event.src_path).name}")
            self.ingestion.ingest_file(Path(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        """Triggered when a file is deleted."""
        if not event.is_directory and self._is_supported_file(event.src_path):
            print(f"\n🗑️  File deleted: {Path(event.src_path).name}")
            self.ingestion.remove_file(Path(event.src_path))


class WatcherService:
    """Service voor het monitoren van de data directory."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = r"C:\Notes"
        self.data_dir = Path(data_dir)
        self.ingestion = DocumentIngestion(data_dir=str(self.data_dir))
        self.event_handler = KnowledgeBaseEventHandler(self.ingestion)
        self.observer = Observer()
        
        print(f"✓ WatcherService initialized")
        print(f"  - Watching directory: {self.data_dir.absolute()} (including subdirectories)")
    
    def start(self, initial_ingest: bool = True):
        """Start de watcher service."""
        print(f"🚀 Watcher Service Starting...", flush=True)
        
        # Eerst een initiële ingest doen van alle bestaande bestanden
        if initial_ingest:
            print("\n🔄 Performing initial ingestion...", flush=True)
            self.ingestion.ingest_directory()
        
        # Start de observer
        self.observer.schedule(
            self.event_handler,
            str(self.data_dir.absolute()),
            recursive=True
        )
        self.observer.start()
        
        print(f"\n👀 Watcher is now monitoring: {self.data_dir.absolute()}", flush=True)
        print("   Running in background mode...\n", flush=True)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping watcher...", flush=True)
            self.stop()
    
    def stop(self):
        """Stop de watcher service."""
        self.observer.stop()
        self.observer.join()
        print("✓ Watcher stopped")


if __name__ == "__main__":
    # Start de watcher service
    watcher = WatcherService()
    watcher.start()
