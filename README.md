# Local Knowledge Base MCP Server

A **Model Context Protocol (MCP) Server** that acts as a bridge between local documentation and Large Language Models via RAG (Retrieval-Augmented Generation). Features **citation-enforced grounding** with local Ollama LLM for fully offline RAG queries.

---

## ⚡ Quickstart

```powershell
# View database stats
.\tasks.ps1 stats

# Start GUI (recommended)
.\tasks.ps1 gui

# Or start file watcher for auto-indexing
.\tasks.ps1 watcher
```

> 📖 **Full operations guide:** See [OPERATIONS.md](OPERATIONS.md)

### Watcher vs Full Re-Ingest

| Mode | When to use |
|------|-------------|
| **Watcher** (`.\tasks.ps1 watcher`) | Daily use - auto-indexes new/changed/deleted files in real-time |
| **Full Re-Ingest** (`.\tasks.ps1 reindex`) | After folder restructure, DB corruption, or embedding model change |

The watcher monitors `C:\Notes` and triggers incremental updates. Full re-ingest rebuilds the entire database (~35k chunks, takes a few minutes).

---

## 🎯 Features

- ✅ **Supported file types:** Markdown (.md), Text (.txt), PDF (.pdf)
- 🔍 **Contextual search:** Natural language queries via ChromaDB
- 📁 **Data source:** Reads from `C:\Notes` directory (configurable)
- 🚀 **MCP Protocol:** Standard interface for LLM clients (Claude Desktop, etc.)
- 💾 **Local vector database:** ChromaDB (no external server required)
- 🧠 **Local embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- 🦙 **Grounded Ollama RAG:** Citation-enforced answers with `[chunk:<id>]` references
- 🔒 **Anti-hallucination:** Rejects answers without valid citations
- 👀 **File watcher:** Real-time monitoring and auto-indexing

## 📋 Requirements

- **Python 3.12** (tested with 3.12.9)
- **Windows 11** (also works on macOS/Linux with path adjustments)
- **Ollama** running locally at `http://localhost:11434`

## 🚀 Installation

### 1. Clone and setup Python environment

```powershell
git clone https://github.com/stallieman/Memory_Vault_Local.git
cd Memory_Vault_Local

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Setup Ollama with grounded model

```powershell
# Pull base model
ollama pull mistral-nemo:12b-instruct-2407-q4_K_M

# Create grounded RAG model with citation enforcement
ollama create rag-grounded-nemo -f .\ollama\Modelfile.rag-grounded
```

### 3. Verify Ollama is running

```powershell
# Check Ollama API
curl http://localhost:11434/api/tags

# Or in PowerShell:
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
```

### 4. Index your documents

Ensure your notes are in `C:\Notes` (or update the path in `src/ingestion.py`).

```powershell
python .\src\ingestion.py
```

## 💡 Usage

### 1. Grounded RAG (Recommended - Citation Enforced)

Query your knowledge base with enforced citations:

```powershell
python .\src\local_rag_ollama.py
```

Features:
- **Citation validation:** Answers must include `[chunk:<id>]` references
- **Auto-retry:** Invalid answers trigger a stricter re-prompt
- **No hallucinations:** Model cannot invent sources or citations
- **IDK response:** If answer not in context, returns exactly: `I don't know based on the provided context.`

**Example session:**
```
======================================================================
Grounded Local RAG with Ollama + C:\Notes
Citation-enforced answers from your knowledge base
======================================================================

✓ Ollama is running at http://localhost:11434
📦 Using model: rag-grounded-nemo

📚 Initializing knowledge base...
✓ Ready!
  - Database: 31,556 chunks indexed
  - Model: rag-grounded-nemo

Question: Hoe maak ik een Docker container?

🔍 Searching knowledge base...
✓ Found 4 relevant chunks.
  Allowed chunk IDs: abc123_0001, abc123_0002, def456_0001, ghi789_0003

🤖 Asking rag-grounded-nemo...

======================================================================
✓ Answer (validated):
----------------------------------------------------------------------
Je kunt een Docker container maken met het `docker run` commando [chunk:abc123_0001].
Bijvoorbeeld: `docker run -d nginx` start een nginx container in detached mode [chunk:abc123_0002].
----------------------------------------------------------------------
Citations used: abc123_0001, abc123_0002
======================================================================
```

### 2. MCP Server (for Claude Desktop)

```powershell
python .\src\server.py
```

Exposes these tools:
- `query_knowledge_base`: Search the knowledge base
- `get_chunk_by_id`: Retrieve full chunk text by ID
- `get_knowledge_base_stats`: Get statistics
- `refresh_knowledge_base`: Re-index all documents

### 3. File Watcher (for continuous sync)

```powershell
python .\src\watcher.py
```

Monitors `C:\Notes` for changes and auto-indexes new/modified files.

### 4. Standalone Ingestion

```powershell
python .\src\ingestion.py
```

One-time indexing of all documents in `C:\Notes`.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `rag-grounded-nemo` | Model to use for RAG |
| `RAG_TOP_K` | `4` | Number of chunks to retrieve |
| `RAG_TOP_K_FULL` | `2` | Number of chunks with full text |
| `RAG_MAX_CHARS_FULL` | `4500` | Max chars per full chunk |
| `RAG_SNIPPET_CHARS` | `400` | Max chars for snippet chunks |
| `RAG_NUM_CTX` | `8192` | Context window size |

### Claude Desktop Configuration

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "local-knowledge-base": {
      "command": "C:\\Projecten\\Memory_Vault_Local\\venv\\Scripts\\python.exe",
      "args": ["C:\\Projecten\\Memory_Vault_Local\\src\\server.py"],
      "cwd": "C:\\Projecten\\Memory_Vault_Local"
    }
  }
}
```

## 📁 Project Structure

```
Memory_Vault_Local/
├── src/
│   ├── __init__.py
│   ├── ingestion.py         # Document ingestion pipeline
│   ├── local_rag_ollama.py  # Grounded RAG with citation validation
│   ├── watcher.py           # File system watcher
│   └── server.py            # MCP server
├── ollama/
│   └── Modelfile.rag-grounded  # Custom Ollama model definition
├── data/                    # Example documents
├── venv/                    # Python virtual environment
├── requirements.txt
└── README.md

# Data source: C:\Notes (all subdirectories)
# Database: C:\Users\<user>\.local-mcp-kb\chroma_db\
```

## 🦙 Ollama Grounded Model

The `rag-grounded-nemo` model is configured with a system prompt that enforces:

1. **Context-only answers:** Must use only provided CONTEXT
2. **Citation format:** Every claim needs `[chunk:<id>]` reference
3. **No fabrication:** Cannot invent books, authors, URLs, page numbers
4. **IDK response:** Must say exactly `I don't know based on the provided context.` when answer not found
5. **Dutch output:** Responses are in Dutch

### Custom Model Creation

```powershell
# View the Modelfile
Get-Content .\ollama\Modelfile.rag-grounded

# Recreate the model (if needed)
ollama create rag-grounded-nemo -f .\ollama\Modelfile.rag-grounded

# List available models
ollama list
```

## 🧪 Acceptance Tests

### 1. Verify Ollama is running

```powershell
curl http://localhost:11434/api/tags
```

Expected: JSON response with list of models including `rag-grounded-nemo`.

### 2. Test ingestion

```powershell
python .\src\ingestion.py
```

Expected: Shows indexed file count and chunk count from `C:\Notes`.

### 3. Test watcher

```powershell
python .\src\watcher.py
```

Expected: Starts monitoring `C:\Notes` for changes.

### 4. Test grounded RAG

```powershell
python .\src\local_rag_ollama.py
```

Expected behavior:
- ✅ Answers contain `[chunk:<id>]` citations
- ✅ Citations reference only provided chunk IDs
- ✅ No invented books/pages/URLs appear
- ✅ Unknown questions return: `I don't know based on the provided context.`

## 🔍 Available MCP Tools

### query_knowledge_base
Search the knowledge base using natural language.
- `query` (string, required): The search query
- `n_results` (number, optional): Number of results (default: 5)
- `return_json` (boolean, optional): Include JSON response (default: true)

### get_chunk_by_id
Retrieve a specific chunk by ID.
- `id` (string, required): The chunk ID
- `max_chars` (number, optional): Max text length (default: 5000)
- `format` (string, optional): `markdown` or `raw` (default: raw)

### get_knowledge_base_stats
Get statistics about the indexed documents.

### refresh_knowledge_base
Re-index all documents in `C:\Notes`.

## 🛠️ Technical Stack

- **Language:** Python 3.12
- **Protocol:** MCP (Model Context Protocol)
- **Vector Database:** ChromaDB
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **LLM:** Ollama with grounded model
- **File Watcher:** watchdog
- **Text Splitting:** langchain-text-splitters
- **PDF Processing:** pypdf

## 📝 License

MIT License

## 🤝 Contributing

Suggestions and improvements are welcome!
