# Project: Local Knowledge Base MCP Server

## 1. Projectbeschrijving
Het doel van dit project is het bouwen van een **Model Context Protocol (MCP) Server** die fungeert als een brug tussen een lokale documentatie-folder en een Large Language Model (LLM).

We gebruiken **RAG (Retrieval-Augmented Generation)**. De applicatie indexeert lokale bestanden en maakt deze doorzoekbaar voor de LLM. Dit stelt de gebruiker in staat om te "chatten" met zijn eigen bibliotheek.

## 2. Requirements

### Functionele Eisen
1.  **Bestandsondersteuning:** Markdown (.md), Text (.txt), en PDF (.pdf).
2.  **Contextueel Zoeken:** Vragen stellen in natuurlijke taal.
3.  **Automatische Synchronisatie (The Watcher):**
    * De map `./data` wordt continu gemonitord.
    * Nieuw bestand -> Direct indexeren.
    * Aangepast bestand -> Index updaten.
    * Verwijderd bestand -> Data verwijderen uit index.
4.  **Interface:** MCP-protocol (JSON-RPC) voor connectie met clients (zoals Claude Desktop of eigen UI).

### Technische Stack
* **Taal:** Python 3.10+
* **Protocol:** `mcp` (Python SDK)
* **Vector Database:** `ChromaDB` (Lokaal, geen server nodig)
* **Watcher:** `watchdog` library voor file system events
* **Embeddings:** `sentence-transformers` (Lokaal model: all-MiniLM-L6-v2)

## 3. Architectuur

### High-Level Diagram
[ ./data Folder ] <--- (Watchdog Event) ---> [ Ingestion Pipeline ] ---> [ ChromaDB ] <--- [ MCP Server ] <---> [ LLM Client ]

### Componenten
1.  **Watcher Service:** Draait in de achtergrond, luistert naar OS-events in de `./data` map.
2.  **Ingestion Pipeline:** Leest bestand -> Chunks (tekst opknippen) -> Embeddings (vectoren maken).
3.  **Vector Store (ChromaDB):** Slaat de vectoren en metadata op.
4.  **MCP Tools:** Exposeert de functie `query_knowledge_base(vraag)` aan de LLM.

## 4. Roadmap

* **Fase 1: MVP + Automation**
    * Setup Python omgeving.
    * Implementatie `watchdog` voor de `./data` map.
    * Implementatie `ChromaDB` opslag.
    * Basis MCP server.
* **Fase 2: Cloud Ready**
    * Voorbereiden migratie van lokale map naar S3 Minio Endpoint.
