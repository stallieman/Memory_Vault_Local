# Operations Manual - Memory Vault

> **Snelstart:** Gebruik `.\tasks.ps1 <command>` voor alle operaties.

---

## 📅 Dagelijks Gebruik (Incremental)

De **watcher** monitort `C:\Notes` en indexeert automatisch:
- Nieuwe bestanden (.md, .txt, .pdf)
- Gewijzigde bestanden (update in ChromaDB)
- Verwijderde bestanden (removal uit ChromaDB)

**Workflow:**
```powershell
# Start watcher (laat draaien in achtergrond)
.\tasks.ps1 watcher

# Of: start GUI voor interactieve queries
.\tasks.ps1 gui
```

Je hoeft **niets handmatig te doen** zolang de watcher draait.

---

## 🔄 Wanneer Full Re-Ingest Nodig Is

Gebruik `.\tasks.ps1 reindex` alleen bij:

| Situatie | Reden |
|----------|-------|
| Mapstructuur gewijzigd | source_group metadata moet opnieuw |
| Veel bestanden hernoemd | Oude entries blijven anders in DB |
| ChromaDB corrupt | Na crash of handmatig verwijderen |
| Embedding model gewijzigd | Vectoren zijn incompatibel |
| Eerste keer setup | Database is leeg |

⚠️ **Let op:** Full re-ingest duurt lang bij veel bestanden (~35k chunks = ~5 min).

---

## ▶️ Start/Stop Commando's

Alle commando's vanuit repo root (`c:\Projecten\memory-vault-main\memory-vault-main`):

| Commando | Beschrijving |
|----------|--------------|
| `.\tasks.ps1 watcher` | Start file watcher (foreground) |
| `.\tasks.ps1 gui` | Start GUI applicatie |
| `.\tasks.ps1 cli` | Start CLI (interactief) |
| `.\tasks.ps1 server` | Start MCP server |
| `.\tasks.ps1 stats` | Toon DB statistieken |
| `.\tasks.ps1 reindex` | Full re-ingest (met confirmatie) |
| `.\tasks.ps1 sanity` | Run sanity check |

**Handmatig (indien tasks.ps1 niet werkt):**
```powershell
cd c:\Projecten\memory-vault-main\memory-vault-main
.\venv\Scripts\Activate.ps1

# Kies één:
python src\watcher.py      # Watcher
python src\rag_gui.py      # GUI
python src\local_rag_ollama.py  # CLI
python src\server.py       # MCP Server
```

---

## 🩺 Health Check / Sanity Check

```powershell
# Quick stats
.\tasks.ps1 stats

# Volledige sanity check (3 test queries)
.\tasks.ps1 sanity
```

**Verwachte output stats:**
```
Total chunks: ~35000
Collection: knowledge_base
Data dir: C:\Notes
DB path: C:\Users\MarcoLocalAdmin\.local-mcp-kb\chroma_db
```

**Sanity check test queries:**
- "CTE join SQL query" → verwacht sql groep dominant
- "TDV caching performance" → verwacht tdv groep dominant  
- "ILM policy Elasticsearch" → verwacht elastic groep dominant

---

## 🔧 Troubleshooting

### Ollama niet bereikbaar
```
✗ Ollama not reachable at http://localhost:11434
```
**Oplossing:** Start Ollama app of `ollama serve`

### Module not found
```
ModuleNotFoundError: No module named 'chromadb'
```
**Oplossing:** Activeer venv eerst:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Watcher ziet wijzigingen niet
**Oplossing:** Controleer of watcher draait en data dir klopt:
```powershell
.\tasks.ps1 stats  # Check "Data dir" output
```

### GUI start niet (customtkinter)
```powershell
.\venv\Scripts\Activate.ps1
pip install customtkinter CTkMessagebox
```

### ChromaDB corrupt / rare resultaten
```powershell
# Backup eerst!
.\tasks.ps1 reindex  # Volledige re-ingest
```

---

## 📁 Belangrijke Paden

| Item | Pad |
|------|-----|
| Data directory | `C:\Notes` |
| ChromaDB | `C:\Users\MarcoLocalAdmin\.local-mcp-kb\chroma_db` |
| Virtual env | `.\venv\` |
| Config | Zie environment variables in README.md |
