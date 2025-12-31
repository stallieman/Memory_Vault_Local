# Local Knowledge Base MCP Server

A **Model Context Protocol (MCP) Server** that acts as a bridge between local documentation and Large Language Models via RAG (Retrieval-Augmented Generation).

## 🎯 Features

- ✅ **Supported file types:** Markdown (.md), Text (.txt), PDF (.pdf)
- 🔍 **Contextual search:** Natural language queries
- 👀 **Automatic synchronization:** Real-time monitoring of the `./data` directory
- 🚀 **MCP Protocol:** Standard interface for LLM clients
- 💾 **Local vector database:** ChromaDB (no external server required)
- 🧠 **Local embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- 🔄 **Auto-start watcher:** Automatic background service via LaunchAgent

## 📋 Requirements

- Python 3.10 or higher
- pip
- macOS (for LaunchAgent auto-start feature)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/stallieman/memory-vault.git
cd memory-vault
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

3. Install the automatic watcher service (macOS only):
```bash
cp com.local-mcp-kb.watcher.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist
```

## 💡 Usage

### 1. MCP Server (for use with Claude Desktop or other MCP clients)

```bash
python src/server.py
```

The MCP server:
- Performs initial ingestion of all files in `./data`
- Starts an MCP server that communicates via stdio
- Exposes the following tools:
  - `query_knowledge_base`: Search the knowledge base
  - `get_knowledge_base_stats`: Get statistics
  - `refresh_knowledge_base`: Re-index all documents

### 2. File Watcher (for continuous synchronization)

The watcher runs automatically in the background after installation. To start manually:

```bash
python src/watcher.py
```

The watcher:
- Performs initial ingestion
- Continuously monitors the `./data` directory
- Automatically indexes new files
- Updates modified files
- Removes deleted files from the index

### 3. Standalone Ingestion (for one-time indexing)

```bash
python src/ingestion.py
```

## 🔧 Configuration for Claude Desktop

Add the following to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "local-knowledge-base": {
      "command": "/absolute/path/to/memory-vault/.venv/bin/python",
      "args": ["/absolute/path/to/memory-vault/src/server.py"],
      "cwd": "/absolute/path/to/memory-vault"
    }
  }
}
```

**Note:** Replace `/absolute/path/to/memory-vault` with the actual absolute path to your project directory.

## 📁 Project Structure

```
memory-vault/
├── data/                    # Your documents (markdown, txt, pdf)
│   ├── docker_cheatsheet.md
│   ├── python_api_project.md
│   ├── AI Engineering.pdf
│   └── ...
├── src/
│   ├── __init__.py
│   ├── ingestion.py         # Document ingestion pipeline
│   ├── watcher.py           # File system watcher
│   └── server.py            # MCP server
├── requirements.txt
├── README.md
├── status.sh                # Check watcher status
├── run_server.sh            # Start MCP server
├── run_watcher.sh           # Start watcher manually
└── com.local-mcp-kb.watcher.plist  # LaunchAgent configuration

# Database location: ~/.local-mcp-kb/chroma_db/ (auto-created in home directory)
```

## 🎓 Example Usage with Claude

After configuration, you can ask questions in Claude Desktop like:

- "What are the main Docker commands?"
- "How do I create a Python API?"
- "Show me the Git cheatsheet"
- "What are the best practices for pandas?"

Claude will automatically use the `query_knowledge_base` tool to retrieve relevant information from your local documents.

## 🔍 Available Tools

### query_knowledge_base
Search the knowledge base using natural language.

**Parameters:**
- `query` (string, required): The search query
- `n_results` (number, optional): Number of results (default: 5)

### get_knowledge_base_stats
Get statistics about the knowledge base.

### refresh_knowledge_base
Re-index all documents in the `./data` directory.

## 🛠️ Technical Stack

- **Language:** Python 3.10+
- **Protocol:** MCP (Model Context Protocol)
- **Vector Database:** ChromaDB
- **File Watcher:** watchdog
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Text Splitting:** langchain-text-splitters
- **PDF Processing:** pypdf

## 📊 Watcher Service Management

**Check status:**
```bash
./status.sh
```

**Stop watcher:**
```bash
launchctl unload ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist
```

**Start watcher:**
```bash
launchctl load ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist
```

**View logs:**
```bash
tail -f ~/.local-mcp-kb/watcher.log
```

## 🚀 Adding New Documents

Simply copy new `.md`, `.txt`, or `.pdf` files to the `data/` directory. The watcher service will automatically detect and index them within 1-2 seconds!

```bash
cp ~/Downloads/new-book.pdf ./data/
# Automatically indexed!
```

## 📝 License

MIT License

## 🤝 Contributing

Suggestions and improvements are welcome!
