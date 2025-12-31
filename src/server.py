"""
MCP Server voor Local Knowledge Base
Exposeert query_knowledge_base tool aan LLM clients via het Model Context Protocol.
"""

import asyncio
import json
from pathlib import Path
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
from ingestion import DocumentIngestion


def _safe_get(d: dict, key: str, default: str = "") -> str:
    """Safely get a value from dict, converting to string."""
    v = d.get(key, default)
    return "" if v is None else str(v)


def make_snippet(text: str, max_len: int = 400) -> str:
    """Create a short snippet from text, removing newlines."""
    s = (text or "").strip().replace("\n", " ")
    if len(s) > max_len:
        return s[:max_len].rstrip() + "…"
    return s


def compact_metadata(metadata: dict) -> dict:
    """Keep only small, useful metadata fields."""
    allow = {
        "filename", "relative_path", "file_type",
        "chunk_id", "total_chunks",
        "source", "doc_id",
        "h1", "h2", "h3", "title",
        "start_char", "end_char"
    }
    return {k: v for k, v in metadata.items() if k in allow}


def format_citation(metadata: dict) -> str:
    """
    Returns a compact citation block with file info and heading context.
    Uses enhanced metadata fields from ingestion.
    """
    filename = _safe_get(metadata, "filename")
    rel = _safe_get(metadata, "relative_path")
    source = _safe_get(metadata, "source")
    file_type = _safe_get(metadata, "file_type")
    chunk_id = _safe_get(metadata, "chunk_id")
    total = _safe_get(metadata, "total_chunks")
    doc_id = _safe_get(metadata, "doc_id")
    
    # Heading context from enhanced metadata
    h1 = _safe_get(metadata, "h1")
    h2 = _safe_get(metadata, "h2")
    h3 = _safe_get(metadata, "h3")
    title = _safe_get(metadata, "title")
    
    # Character offsets
    start_char = _safe_get(metadata, "start_char")
    end_char = _safe_get(metadata, "end_char")
    
    parts = []
    
    # File identification
    if rel:
        parts.append(f"path={rel}")
    elif filename:
        parts.append(f"file={filename}")
    
    # Document and chunk info
    if doc_id:
        parts.append(f"doc_id={doc_id}")
    if chunk_id != "":
        chunk_info = f"chunk={chunk_id}/{total}" if total else f"chunk={chunk_id}"
        parts.append(chunk_info)
    
    # Heading hierarchy for context
    if h1 or h2 or h3:
        heading_parts = [p for p in [h1, h2, h3] if p]
        heading = " > ".join(heading_parts)
        parts.append(f"section=\"{heading}\"")
    elif title:
        parts.append(f"title=\"{title}\"")
    
    # Character position for precise citation
    if start_char and end_char:
        parts.append(f"chars={start_char}-{end_char}")
    
    return " | ".join(parts)


class KnowledgeBaseMCPServer:
    """MCP Server voor knowledge base queries."""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = str(Path.home() / "notes")
        self.data_dir = Path(data_dir)
        self.ingestion = DocumentIngestion(data_dir=str(self.data_dir))
        self.server = Server("local-knowledge-base")
        
        # Setup handlers
        self._setup_handlers()
        
        print(f"✓ MCP Server initialized")
        print(f"  - Data directory: {self.data_dir.absolute()}")
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="query_knowledge_base",
                    description=(
                        "Zoek in de lokale knowledge base met natuurlijke taal. "
                        "Deze tool doorzoekt alle geïndexeerde documenten (markdown, txt) "
                        "en retourneert de meest relevante passages met snippets en IDs. "
                        "Gebruik daarna get_chunk_by_id met de ID van het beste resultaat "
                        "om de volledige tekst op te halen voordat je een definitief antwoord geeft. "
                        "Gebruik deze tool om informatie op te halen uit cheatsheets, "
                        "documentatie en andere lokaal opgeslagen kennisbestanden."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "De zoekvraag in natuurlijke taal"
                            },
                            "n_results": {
                                "type": "number",
                                "description": "Aantal resultaten (standaard: 5)",
                                "default": 5
                            },
                            "snippet_chars": {
                                "type": "number",
                                "description": "Max lengte van snippet per resultaat (default: 400)",
                                "default": 400
                            },
                            "include_full_text": {
                                "type": "boolean",
                                "description": "Als true: voeg volledige chunk-tekst toe in Markdown (default: false)",
                                "default": False
                            },
                            "return_json": {
                                "type": "boolean",
                                "description": "Als true: voeg ook machine-readable JSON toe (structuredContent + JSON tekstblock)",
                                "default": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_chunk_by_id",
                    description=(
                        "Haal één specifieke chunk op uit de knowledge base op basis van chunk ID. "
                        "Gebruik dit nadat query_knowledge_base een relevant resultaat teruggeeft, "
                        "om de volledige tekst en metadata van die chunk op te halen."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "De chunk ID zoals teruggegeven in query_knowledge_base (items[].id)"
                            },
                            "max_chars": {
                                "type": "number",
                                "description": "Maximaal aantal tekens van de chunk-tekst om terug te geven (default: 5000)",
                                "default": 5000
                            },
                            "format": {
                                "type": "string",
                                "description": "Output formaat. 'markdown' geeft headers + cite-blok; 'raw' geeft alleen de chunk tekst.",
                                "enum": ["markdown", "raw"],
                                "default": "raw"
                            },
                            "return_json": {
                                "type": "boolean",
                                "description": "Als true: voeg structuredContent + JSON tekstblock toe (default: true).",
                                "default": True
                            }
                        },
                        "required": ["id"]
                    }
                ),
                types.Tool(
                    name="get_knowledge_base_stats",
                    description=(
                        "Haal statistieken op over de knowledge base, "
                        "zoals aantal geïndexeerde documenten en chunks."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="refresh_knowledge_base",
                    description=(
                        "Ververs de knowledge base door alle documenten opnieuw te indexeren. "
                        "Gebruik dit als je denkt dat de index niet meer up-to-date is."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: dict[str, Any]
        ) -> list[types.TextContent]:
            """Handle tool calls."""
            
            if name == "query_knowledge_base":
                query = arguments.get("query", "")
                n_results = arguments.get("n_results", 5)
                snippet_chars = int(arguments.get("snippet_chars", 400))
                include_full_text = bool(arguments.get("include_full_text", False))
                return_json = arguments.get("return_json", True)
                
                if not query:
                    return [types.TextContent(
                        type="text",
                        text="Error: Query parameter is required"
                    )]
                
                # Perform query
                results = self.ingestion.query(query, n_results=n_results)
                
                if results['count'] == 0:
                    return [types.TextContent(
                        type="text",
                        text=f"Geen resultaten gevonden voor: '{query}'"
                    )]
                
                # Build structured data with lightweight JSON
                items = []
                response = f"# Zoekresultaten voor: '{query}'\n\n"
                response += f"Gevonden {results['count']} relevante passages:\n\n"
                
                for rank, (doc, metadata, distance, doc_id) in enumerate(zip(
                    results['results']['documents'][0],
                    results['results']['metadatas'][0],
                    results['results']['distances'][0],
                    results['results']['ids'][0]
                ), 1):
                    citation = format_citation(metadata)
                    score = 1 - float(distance)
                    
                    # Create snippet for both Markdown and JSON
                    snippet = make_snippet(doc, snippet_chars)
                    
                    # Build Markdown response (snippet-only by default)
                    response += f"## Resultaat {rank}\n"
                    response += f"**ID:** `{doc_id}`\n"
                    response += f"**Cite:** {citation}\n"
                    response += f"**Score:** {score:.2%}\n\n"
                    response += f"{snippet}\n\n"
                    
                    # Optionally include full text in collapsible section
                    if include_full_text:
                        full = (doc or "").strip()
                        if len(full) > 1500:
                            full = full[:1500].rstrip() + "…"
                        response += "<details><summary>Full text</summary>\n\n"
                        response += f"{full}\n\n"
                        response += "</details>\n\n"
                    
                    response += "---\n\n"
                    
                    # Build lightweight structured item
                    items.append({
                        "rank": rank,
                        "id": doc_id,  # Chroma chunk ID for retrieval
                        "score": score,
                        "snippet": snippet,
                        "citation": citation,
                        "metadata": compact_metadata(metadata),
                    })
                
                # Build lightweight JSON payload
                payload = {
                    "query": query,
                    "n_results": n_results,
                    "count": results["count"],
                    "items": items,
                    "truncated": False,
                }
                
                # Return both Markdown and JSON
                if return_json:
                    return [
                        types.TextContent(type="text", text=response),
                        types.TextContent(
                            type="text",
                            text=f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
                        ),
                    ]
                else:
                    return [types.TextContent(type="text", text=response)]
            
            elif name == "get_chunk_by_id":
                chunk_id = arguments.get("id", "")
                max_chars = int(arguments.get("max_chars", 5000))
                fmt = arguments.get("format", "raw")
                return_json = arguments.get("return_json", True)
                
                # Validate format
                if fmt not in ("markdown", "raw"):
                    fmt = "raw"
                
                if not chunk_id:
                    return [types.TextContent(
                        type="text",
                        text="Error: id parameter is required"
                    )]
                
                # Get chunk by ID from ChromaDB
                try:
                    res = self.ingestion.collection.get(
                        ids=[chunk_id],
                        include=["documents", "metadatas"]
                    )
                    
                    if not res or not res.get("ids"):
                        return [types.TextContent(
                            type="text",
                            text=f"Chunk not found: {chunk_id}"
                        )]
                    
                    doc = (res.get("documents") or [""])[0] or ""
                    meta = (res.get("metadatas") or [{}])[0] or {}
                    
                    # Truncate doc for safety
                    doc = doc.strip()
                    truncated = False
                    if max_chars and len(doc) > max_chars:
                        doc = doc[:max_chars].rstrip() + "…"
                        truncated = True
                    
                    citation = format_citation(meta)
                    
                    # Build output based on format
                    if fmt == "raw":
                        # Only the text, useful for Claude to process context directly
                        text_out = doc
                    else:
                        # Markdown with metadata/citation
                        text_out = "# Chunk\n\n"
                        text_out += f"**ID:** {chunk_id}\n\n"
                        text_out += f"**Cite:** {citation}\n\n"
                        text_out += "## Text\n\n"
                        text_out += f"{doc}\n"
                    
                    # Machine-readable payload (small but complete)
                    payload = {
                        "id": chunk_id,
                        "format": fmt,
                        "citation": citation,
                        "metadata": compact_metadata(meta),
                        "snippet": make_snippet(doc, 400),
                        "truncated": truncated,
                    }
                    
                    # Return as text always; add JSON text when requested
                    if return_json:
                        return [
                            types.TextContent(type="text", text=text_out),
                            types.TextContent(
                                type="text",
                                text=f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
                            ),
                        ]
                    
                    return [types.TextContent(type="text", text=text_out)]
                    
                except Exception as e:
                    return [types.TextContent(
                        type="text",
                        text=f"Error fetching chunk '{chunk_id}': {e}"
                    )]
            
            elif name == "get_knowledge_base_stats":
                stats = self.ingestion.get_stats()
                
                response = "# Knowledge Base Statistieken\n\n"
                response += f"- **Totaal chunks:** {stats['total_chunks']}\n"
                response += f"- **Collection:** {stats['collection_name']}\n"
                response += f"- **Data directory:** {stats['data_directory']}\n"
                response += f"- **Database path:** {stats['db_path']}\n"
                
                return [types.TextContent(type="text", text=response)]
            
            elif name == "refresh_knowledge_base":
                count = self.ingestion.ingest_directory()
                
                response = f"# Knowledge Base Refresh Compleet\n\n"
                response += f"✓ {count} bestanden opnieuw geïndexeerd\n"
                response += f"Totaal chunks in database: {self.ingestion.collection.count()}\n"
                
                return [types.TextContent(type="text", text=response)]
            
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            print("🚀 MCP Server running...")
            print("   Waiting for client connections...")
            
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="local-knowledge-base",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point."""
    server = KnowledgeBaseMCPServer()
    
    # Check if database exists, only ingest if empty
    if server.ingestion.collection.count() == 0:
        print("\n🔄 Database empty, performing initial ingestion...")
        server.ingestion.ingest_directory()
        print()
    else:
        print(f"\n✓ Database ready with {server.ingestion.collection.count()} chunks")
        print()
    
    # Start MCP server
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
