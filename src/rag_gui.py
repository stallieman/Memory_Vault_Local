"""
Grounded RAG GUI Application
A modern Windows GUI for the citation-enforced RAG system.
"""

import os
import sys
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Optional, Set, List, Dict, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

# Import RAG components
from ingestion import DocumentIngestion
from retrieval import GROUP_ORDER, RAG_TOP_K_TOTAL, RAG_TOP_K_PER_GROUP
from local_rag_ollama import (
    OLLAMA_BASE_URL, OLLAMA_MODEL, RAG_TOP_K, RAG_TOP_K_FULL,
    RAG_FILTER_TOC, RAG_PDF_EXPAND, RAG_PDF_EXPAND_RADIUS, RAG_NUM_CTX,
    RAG_MAX_PER_SOURCE,
    IDK, CITATION_PATTERN, CitationValidationError,
    check_ollama_connection, get_effective_model,
    retrieve_context, ask_with_strict_validation
)

# ============================================================================
# App Configuration
# ============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "Memory Vault - Grounded RAG"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800


class RAGApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(800, 600)
        
        # State
        self.kb: Optional[DocumentIngestion] = None
        self.effective_model: str = OLLAMA_MODEL
        self.is_processing = False
        self.response_queue = queue.Queue()
        
        # Build UI
        self._create_widgets()
        self._create_layout()
        
        # Initialize in background
        self.after(100, self._initialize_async)
        
        # Poll for async responses
        self._poll_queue()
    
    def _create_widgets(self):
        """Create all UI widgets."""
        
        # ===== Header Frame =====
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📚 Memory Vault",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Grounded RAG with Citation Enforcement",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        
        # ===== Status Frame =====
        self.status_frame = ctk.CTkFrame(self, corner_radius=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="⏳ Initializing...",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        
        self.model_label = ctk.CTkLabel(
            self.status_frame,
            text="Model: -",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        
        self.chunks_label = ctk.CTkLabel(
            self.status_frame,
            text="Chunks: -",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        
        self.datadir_label = ctk.CTkLabel(
            self.status_frame,
            text="📁 Data: -",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color="gray"
        )
        
        self.dbpath_label = ctk.CTkLabel(
            self.status_frame,
            text="🗄️ DB: -",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color="gray"
        )
        
        # ===== Config Frame =====
        self.config_frame = ctk.CTkFrame(self, corner_radius=10)
        
        self.config_title = ctk.CTkLabel(
            self.config_frame,
            text="⚙️ Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        
        self.toc_filter_var = ctk.BooleanVar(value=RAG_FILTER_TOC)
        self.toc_filter_check = ctk.CTkCheckBox(
            self.config_frame,
            text="Filter TOC chunks",
            variable=self.toc_filter_var
        )
        
        self.pdf_expand_var = ctk.BooleanVar(value=RAG_PDF_EXPAND)
        self.pdf_expand_check = ctk.CTkCheckBox(
            self.config_frame,
            text="Expand PDF chunks",
            variable=self.pdf_expand_var
        )
        
        self.diversity_var = ctk.BooleanVar(value=True)
        self.diversity_check = ctk.CTkCheckBox(
            self.config_frame,
            text=f"Source diversity (max {RAG_MAX_PER_SOURCE}/source)",
            variable=self.diversity_var
        )
        
        # ===== Main Content Frame =====
        self.content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        
        # Chat history
        self.chat_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        
        self.chat_label = ctk.CTkLabel(
            self.chat_frame,
            text="💬 Conversation",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        
        self.chat_textbox = ctk.CTkTextbox(
            self.chat_frame,
            font=ctk.CTkFont(size=13),
            wrap="word",
            state="disabled"
        )
        
        # Sources panel
        self.sources_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        
        self.sources_label = ctk.CTkLabel(
            self.sources_frame,
            text="📎 Sources & Citations",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        
        self.sources_textbox = ctk.CTkTextbox(
            self.sources_frame,
            font=ctk.CTkFont(size=11),
            wrap="word",
            state="disabled",
            width=350
        )
        
        # ===== Input Frame =====
        self.input_frame = ctk.CTkFrame(self, corner_radius=10)
        
        self.question_entry = ctk.CTkTextbox(
            self.input_frame,
            font=ctk.CTkFont(size=14),
            height=80,
            wrap="word"
        )
        self.question_entry.bind("<Control-Return>", self._on_submit)
        self.question_entry.bind("<Shift-Return>", lambda e: None)  # Allow shift+enter for newline
        
        self.submit_button = ctk.CTkButton(
            self.input_frame,
            text="🔍 Ask Question",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_submit
        )
        
        self.clear_button = ctk.CTkButton(
            self.input_frame,
            text="🗑️ Clear",
            font=ctk.CTkFont(size=12),
            height=40,
            width=80,
            fg_color="gray",
            command=self._clear_chat
        )
        
        self.hint_label = ctk.CTkLabel(
            self.input_frame,
            text="Press Ctrl+Enter to submit",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        
        # ===== Progress =====
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate", height=3)
    
    def _create_layout(self):
        """Arrange widgets in the window."""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Content row expands
        
        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.title_label.pack(side="left", padx=10)
        self.subtitle_label.pack(side="left", padx=10, pady=(8, 0))
        
        # Status bar
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        self.status_label.pack(side="left", padx=15, pady=8)
        self.model_label.pack(side="left", padx=15, pady=8)
        self.chunks_label.pack(side="left", padx=15, pady=8)
        self.datadir_label.pack(side="left", padx=15, pady=8)
        self.dbpath_label.pack(side="left", padx=15, pady=8)
        
        # Config (collapsible)
        self.config_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        self.config_title.pack(side="left", padx=15, pady=8)
        self.toc_filter_check.pack(side="left", padx=15, pady=8)
        self.pdf_expand_check.pack(side="left", padx=15, pady=8)
        self.diversity_check.pack(side="left", padx=15, pady=8)
        
        # Main content
        self.content_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Chat area
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(1, weight=1)
        self.chat_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        self.chat_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Sources panel
        self.sources_frame.grid(row=0, column=1, sticky="nsew")
        self.sources_frame.grid_rowconfigure(1, weight=1)
        self.sources_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        self.sources_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Input area
        self.input_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(5, 20))
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.question_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10, rowspan=2)
        self.submit_button.grid(row=0, column=1, padx=10, pady=(10, 5))
        self.clear_button.grid(row=1, column=1, padx=10, pady=(5, 10))
        self.hint_label.grid(row=2, column=0, columnspan=2, pady=(0, 5))
        
        # Progress bar (hidden initially)
        self.progress_bar.grid(row=5, column=0, sticky="ew", padx=20)
        self.progress_bar.grid_remove()
    
    def _initialize_async(self):
        """Initialize knowledge base in background thread."""
        def init_worker():
            try:
                # Check Ollama
                self.response_queue.put(("status", "🔍 Connecting to Ollama..."))
                is_connected, models = check_ollama_connection()
                
                if not is_connected:
                    self.response_queue.put(("error", "Cannot connect to Ollama. Is it running?"))
                    return
                
                # Get model
                model = get_effective_model(models)
                self.response_queue.put(("model", model))
                
                # Initialize KB
                self.response_queue.put(("status", "📚 Loading knowledge base..."))
                kb = DocumentIngestion()
                stats = kb.get_stats()
                
                self.response_queue.put(("kb_ready", (kb, stats)))
                
            except Exception as e:
                self.response_queue.put(("error", str(e)))
        
        thread = threading.Thread(target=init_worker, daemon=True)
        thread.start()
    
    def _poll_queue(self):
        """Poll the response queue for async updates."""
        try:
            while True:
                msg_type, data = self.response_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_label.configure(text=data)
                
                elif msg_type == "model":
                    self.effective_model = data
                    self.model_label.configure(text=f"Model: {data}")
                
                elif msg_type == "kb_ready":
                    kb, stats = data
                    self.kb = kb
                    self.chunks_label.configure(text=f"Chunks: {stats['total_chunks']:,}")
                    self.datadir_label.configure(text=f"📁 {stats['data_directory']}")
                    self.dbpath_label.configure(text=f"🗄️ {stats.get('db_path', 'default')}")
                    self.status_label.configure(text="✅ Ready")
                    self._append_system_message(
                        f"Knowledge base loaded: {stats['total_chunks']:,} chunks from {stats['data_directory']}"
                    )
                
                elif msg_type == "error":
                    self.status_label.configure(text=f"❌ {data}")
                    CTkMessagebox(
                        title="Error",
                        message=data,
                        icon="cancel"
                    )
                
                elif msg_type == "sources":
                    self._update_sources(data)
                
                elif msg_type == "answer":
                    answer, citations = data
                    self._append_answer(answer, citations)
                    self._stop_processing()
                
                elif msg_type == "answer_error":
                    self._append_error(data)
                    self._stop_processing()
                    
        except queue.Empty:
            pass
        
        # Schedule next poll
        self.after(100, self._poll_queue)
    
    def _on_submit(self, event=None):
        """Handle question submission."""
        if self.is_processing:
            return
        
        question = self.question_entry.get("1.0", "end-1c").strip()
        if not question:
            return
        
        if not self.kb:
            CTkMessagebox(
                title="Not Ready",
                message="Knowledge base is still loading. Please wait.",
                icon="warning"
            )
            return
        
        # Clear input and start processing
        self.question_entry.delete("1.0", "end")
        self._start_processing()
        self._append_question(question)
        
        # Run query in background
        def query_worker():
            try:
                # Update config from checkboxes
                import local_rag_ollama as rag
                rag.RAG_FILTER_TOC = self.toc_filter_var.get()
                rag.RAG_PDF_EXPAND = self.pdf_expand_var.get()
                # Source diversity: set to high number if disabled
                rag.RAG_MAX_PER_SOURCE = 3 if self.diversity_var.get() else 999
                
                # Retrieve context
                context_chunks, allowed_ids, diagnostics = retrieve_context(self.kb, question)
                
                if not context_chunks:
                    self.response_queue.put(("answer_error", "No relevant documents found in knowledge base."))
                    return
                
                # Show sources
                self.response_queue.put(("sources", (context_chunks, diagnostics)))
                
                # Get answer (use lenient mode for GUI - allows teaching-style answers)
                answer, citations = ask_with_strict_validation(
                    question, context_chunks, allowed_ids, self.effective_model,
                    lenient_mode=True
                )
                
                self.response_queue.put(("answer", (answer, citations)))
                
            except CitationValidationError as e:
                self.response_queue.put(("answer_error", f"Citation validation failed: {e.reason}"))
            except Exception as e:
                self.response_queue.put(("answer_error", f"Error: {str(e)}"))
        
        thread = threading.Thread(target=query_worker, daemon=True)
        thread.start()
    
    def _start_processing(self):
        """Show processing state."""
        self.is_processing = True
        self.submit_button.configure(state="disabled", text="⏳ Processing...")
        self.progress_bar.grid()
        self.progress_bar.start()
    
    def _stop_processing(self):
        """Hide processing state."""
        self.is_processing = False
        self.submit_button.configure(state="normal", text="🔍 Ask Question")
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
    
    def _append_to_chat(self, text: str, tag: str = "normal"):
        """Append text to chat history."""
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.insert("end", text + "\n\n")
        self.chat_textbox.configure(state="disabled")
        self.chat_textbox.see("end")
    
    def _append_system_message(self, message: str):
        """Add a system message."""
        timestamp = datetime.now().strftime("%H:%M")
        self._append_to_chat(f"ℹ️ [{timestamp}] {message}")
    
    def _append_question(self, question: str):
        """Add user question to chat."""
        timestamp = datetime.now().strftime("%H:%M")
        self._append_to_chat(f"👤 [{timestamp}] {question}")
    
    def _append_answer(self, answer: str, citations: Set[str]):
        """Add validated answer to chat."""
        timestamp = datetime.now().strftime("%H:%M")
        citation_text = f"\n📎 Citations: {', '.join(sorted(citations))}" if citations else ""
        self._append_to_chat(f"✅ [{timestamp}] {answer}{citation_text}")
    
    def _append_error(self, error: str):
        """Add error message to chat."""
        timestamp = datetime.now().strftime("%H:%M")
        self._append_to_chat(f"❌ [{timestamp}] {error}")
    
    def _update_sources(self, data: Tuple[List[Dict], dict]):
        """Update the sources panel."""
        chunks, diagnostics = data
        
        self.sources_textbox.configure(state="normal")
        self.sources_textbox.delete("1.0", "end")
        
        # Summary
        text = f"📊 Retrieved: {diagnostics['fetched']} → {diagnostics['final_count']} chunks\n"
        if diagnostics['toc_filtered'] > 0:
            text += f"🗑️ Filtered: {diagnostics['toc_filtered']} TOC chunks\n"
        if diagnostics.get('source_limited'):
            text += f"🎯 Diversity: {len(diagnostics['source_limited'])} limited (max {RAG_MAX_PER_SOURCE}/source)\n"
        if diagnostics.get('sources_used'):
            text += f"📚 Sources: {len(diagnostics['sources_used'])} different files\n"
        if diagnostics['expanded_chunks'] > 0:
            text += f"📖 Expanded: {diagnostics['expanded_chunks']} adjacent chunks\n"
        text += "\n" + "─" * 40 + "\n\n"
        
        # Individual sources
        for chunk in chunks[:10]:
            meta = chunk.get("metadata", {})
            source = meta.get("relative_path", meta.get("filename", "unknown"))
            score = chunk.get("score", 0)
            chunk_id = chunk.get("id", "?")
            expanded = " [expanded]" if chunk.get("expanded") else ""
            
            text += f"📄 {source}\n"
            text += f"   ID: {chunk_id}{expanded}\n"
            text += f"   Score: {score:.2f}\n"
            
            # Preview
            preview = chunk.get("text", "")[:150].replace("\n", " ")
            text += f"   \"{preview}...\"\n\n"
        
        if len(chunks) > 10:
            text += f"... and {len(chunks) - 10} more sources\n"
        
        self.sources_textbox.insert("1.0", text)
        self.sources_textbox.configure(state="disabled")
    
    def _clear_chat(self):
        """Clear chat history."""
        self.chat_textbox.configure(state="normal")
        self.chat_textbox.delete("1.0", "end")
        self.chat_textbox.configure(state="disabled")
        
        self.sources_textbox.configure(state="normal")
        self.sources_textbox.delete("1.0", "end")
        self.sources_textbox.configure(state="disabled")


def main():
    """Launch the application."""
    app = RAGApp()
    app.mainloop()


if __name__ == "__main__":
    main()
