#!/bin/bash
# Status check voor de Local Knowledge Base Watcher Service

echo "📊 Local MCP-KB Watcher Status"
echo "================================"
echo ""

# Check if service is running
if launchctl list | grep -q "com.local-mcp-kb.watcher"; then
    PID=$(launchctl list | grep "com.local-mcp-kb.watcher" | awk '{print $1}')
    echo "✅ Status: RUNNING (PID: $PID)"
else
    echo "❌ Status: NOT RUNNING"
fi

echo ""
echo "📁 Database locatie: ~/.local-mcp-kb/chroma_db/"
echo ""

# Show stats from database
if [ -d "$HOME/.local-mcp-kb/chroma_db" ]; then
    echo "💾 Database bestaat"
    cd "$(dirname "$0")"
    CHUNKS=$(.venv/bin/python -c "from src.ingestion import DocumentIngestion; ing = DocumentIngestion(); print(ing.collection.count())" 2>/dev/null)
    if [ ! -z "$CHUNKS" ]; then
        echo "   Totaal chunks: $CHUNKS"
    fi
else
    echo "⚠️  Database niet gevonden"
fi

echo ""
echo "📋 Recente logs (laatste 10 regels):"
echo "-----------------------------------"
if [ -f "$HOME/.local-mcp-kb/watcher.log" ]; then
    tail -10 "$HOME/.local-mcp-kb/watcher.log"
else
    echo "Geen logs gevonden"
fi

echo ""
echo "🔧 Handige commando's:"
echo "  Start:   launchctl load ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist"
echo "  Stop:    launchctl unload ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist"
echo "  Logs:    tail -f ~/.local-mcp-kb/watcher.log"
echo "  Errors:  tail -f ~/.local-mcp-kb/watcher-error.log"
