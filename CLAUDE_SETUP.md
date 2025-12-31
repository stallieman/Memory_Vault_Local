# Claude Desktop Configuratie

## Stap 1: Vind het absolute pad naar je project

```bash
cd /Users/marcostalman/Projects/local-mcp-kb
pwd
```

Het resultaat is: `/Users/marcostalman/Projects/local-mcp-kb`

## Stap 2: Open Claude Desktop configuratie

Op macOS:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Of handmatig navigeren naar:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## Stap 3: Voeg de MCP server configuratie toe

Voeg het volgende toe aan je `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "local-knowledge-base": {
      "command": "/Users/marcostalman/Projects/local-mcp-kb/.venv/bin/python",
      "args": [
        "/Users/marcostalman/Projects/local-mcp-kb/src/server.py"
      ],
      "cwd": "/Users/marcostalman/Projects/local-mcp-kb",
      "env": {}
    }
  }
}
```

**Belangrijk:** Als je al andere MCP servers hebt geconfigureerd, voeg dan alleen de `"local-knowledge-base"` sectie toe binnen het bestaande `"mcpServers"` object.

## Stap 4: Herstart Claude Desktop

Sluit Claude Desktop volledig af en start het opnieuw.

## Stap 5: Test de configuratie

In Claude Desktop, probeer een vraag zoals:

```
Wat zijn de belangrijkste Docker commando's?
```

Claude zou automatisch de `query_knowledge_base` tool moeten gebruiken en resultaten uit je lokale documenten tonen.

## Voorbeeld vragen

- "Wat zijn de belangrijkste Git commando's?"
- "Hoe werk je met pandas DataFrames?"
- "Toon me de Linux cheatsheet"
- "Wat is het verschil tussen INNER JOIN en LEFT JOIN?"
- "Hoe maak ik een Python API?"

## Troubleshooting

### Server start niet
1. Controleer of het pad correct is (gebruik absolute paden)
2. Controleer of Python en alle dependencies geïnstalleerd zijn
3. Test handmatig: `/Users/marcostalman/Projects/local-mcp-kb/.venv/bin/python /Users/marcostalman/Projects/local-mcp-kb/src/server.py`

### Geen resultaten
1. Controleer of de database bestaat: `ls -la chroma_db/`
2. Run de ingestion handmatig: `/Users/marcostalman/Projects/local-mcp-kb/.venv/bin/python src/ingestion.py`

### Tools worden niet getoond
1. Kijk in de Claude Desktop logs
2. Herstart Claude Desktop volledig
3. Controleer de JSON syntax in de configuratie

## Logs bekijken

Op macOS vind je Claude Desktop logs in:
```
~/Library/Logs/Claude/
```

## Handmatig testen

Je kunt de MCP server ook handmatig testen:

```bash
cd /Users/marcostalman/Projects/local-mcp-kb
/Users/marcostalman/Projects/local-mcp-kb/.venv/bin/python src/server.py
```

Dit zou de server moeten starten en wachten op stdio communicatie.
