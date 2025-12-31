# Local Knowledge Base MCP Server

A **Model Context Protocol (MCP) Server** that acts as a bridge between local documentation and Large Language Models via RAG (Retrieval-Augmented Generation). Now with **local Ollama LLM integration** for fully offline RAG queries.

## 🎯 Features

- ✅ **Supported file types:** Markdown (.md), Text (.txt), PDF (.pdf)
- 🔍 **Contextual search:** Natural language queries via ChromaDB
- 📁 **Data source:** Reads from `C:\Notes` directory (configurable)
- 🚀 **MCP Protocol:** Standard interface for LLM clients (Claude Desktop, etc.)
- 💾 **Local vector database:** ChromaDB (no external server required)
- 🧠 **Local embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- 🦙 **Ollama RAG:** Standalone RAG with local Ollama LLM (no API keys needed!)
- 👀 **File watcher:** Real-time monitoring and auto-indexing

## 📋 Requirements

- **Python 3.12** (tested with 3.12.9)
- **Windows 11** (also works on macOS/Linux with path adjustments)
- **Ollama** running locally at `http://localhost:11434` (for RAG feature)

## 🚀 Installation

1. Clone the repository:
```powershell
git clone https://github.com/stallieman/Memory_Vault_Local.git
cd Memory_Vault_Local
```

2. Create a virtual environment and install dependencies:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Ensure your notes are in `C:\Notes` (or update the path in `src/ingestion.py`)

4. Run initial ingestion:
```powershell
python src/ingestion.py
```

## 💡 Usage

### 1. Ollama RAG (Recommended - Fully Local)

Query your knowledge base using a local Ollama model:

```powershell
python src/local_rag_ollama.py
```

This will:
- Check Ollama connectivity at `http://localhost:11434`
- Auto-detect available models (defaults to `mistral-nemo:12b-instruct-2407-q4_K_M`)
- Start an interactive chat session with RAG

**Example session:**
```
🦙 Ollama RAG - Local Knowledge Base
=====================================
Model: mistral-nemo:12b-instruct-2407-q4_K_M
Database: 31,556 chunks indexed

Vraag: Hoe maak ik een Docker container?

[Searches knowledge base, retrieves context, generates answer...]
```

### 2. MCP Server (for Claude Desktop)

```powershell
python src/server.py
```

Exposes these tools:
- `query_knowledge_base`: Search the knowledge base
- `get_knowledge_base_stats`: Get statistics
- `refresh_knowledge_base`: Re-index all documents

### 3. File Watcher (for continuous sync)

```powershell
python src/watcher.py
```

Monitors `C:\Notes` for changes and auto-indexes new/modified files.

### 4. Standalone Ingestion

```powershell
python src/ingestion.py
```

One-time indexing of all documents in `C:\Notes`.

## 🔧 Configuration for Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

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
│   ├── local_rag_ollama.py  # 🆕 Ollama RAG entrypoint
│   ├── watcher.py           # File system watcher
│   └── server.py            # MCP server
├── data/                    # Example documents
├── venv/                    # Python virtual environment
├── requirements.txt
└── README.md

# Data source: C:\Notes (all subdirectories)
# Database: C:\Users\<user>\.local-mcp-kb\chroma_db\
```

## 🦙 Ollama Setup

1. Install Ollama from https://ollama.ai
2. Pull a model:
```powershell
ollama pull mistral-nemo:12b-instruct-2407-q4_K_M
# Or any other model you prefer
```
3. Ollama runs automatically as a service on `localhost:11434`

## 🎓 Example Queries

After indexing your notes, you can ask:

- "Wat zijn de belangrijkste Docker commands?"
- "Hoe maak ik een Python API?"
- "Leg SQL JOINs uit"
- "Wat zijn de Git best practices?"

The system retrieves relevant chunks from your notes and generates contextual answers.

## 🔍 Available MCP Tools

### query_knowledge_base
Search the knowledge base using natural language.
- `query` (string, required): The search query
- `n_results` (number, optional): Number of results (default: 5)

### get_knowledge_base_stats
Get statistics about the indexed documents.

### refresh_knowledge_base
Re-index all documents in `C:\Notes`.

## 🛠️ Technical Stack

- **Language:** Python 3.12
- **Protocol:** MCP (Model Context Protocol)
- **Vector Database:** ChromaDB
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **LLM:** Ollama (local, any model)
- **File Watcher:** watchdog
- **Text Splitting:** langchain-text-splitters
- **PDF Processing:** pypdf

## 📝 License

MIT License

## 🤝 Contributing

Suggestions and improvements are welcome!
