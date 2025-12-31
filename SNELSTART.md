# 🚀 Snelstart Gids

## ✅ KLAAR! Configuratie is compleet

De configuratie voor Claude Desktop is automatisch ingesteld en de **watcher service draait automatisch op de achtergrond**! 

### 🎯 Automatische Monitoring

De watcher service monitort automatisch de `data/` folder en indexeert:
- ✅ Nieuwe bestanden direct
- ✅ Gewijzigde bestanden automatisch
- ✅ Verwijdert verwijderde bestanden uit de index

**Je hoeft niets te doen!** Voeg gewoon bestanden toe aan `data/` en ze worden automatisch geïndexeerd. 

## Wat nu?

### 1. Herstart Claude Desktop
- Sluit Claude Desktop **volledig** af (Cmd+Q)
- Start Claude Desktop opnieuw op

### 2. Test met een vraag

Open een nieuwe chat in Claude Desktop en stel een van deze vragen:

```
Wat zijn de belangrijkste Docker commando's?
```

```
Hoe werk je met pandas DataFrames?
```

```
Geef me de Git cheatsheet
```

```
Wat is het verschil tussen INNER JOIN en LEFT JOIN?
```

```
Hoe maak ik een Python API?
```

### 3. Hoe herken je dat het werkt?

Wanneer je een vraag stelt, zou je in Claude Desktop moeten zien:
- 🔧 Een notificatie dat Claude de `query_knowledge_base` tool gebruikt
- 📄 Resultaten uit je lokale documenten met bronvermelding (filename)

## 💡 Tips

### Wat kun je vragen?

Je hebt momenteel **18 documenten** geïndexeerd over:
- Docker & Docker Compose
- Git
- Python (API's, file handling, pandas)
- SQL (basic, advanced, CTEs, JOINs)
- Linux & Vim
- Power BI
- Elastic/Logstash
- Keybindings

**Vraag gewoon wat je wilt weten!** Claude zal automatisch je lokale documenten doorzoeken.

### Voorbeelden van goede vragen:

✅ "Hoe maak ik een Docker container?"
✅ "Wat is de pandas syntax voor het filteren van data?"
✅ "Leg me SQL CTEs uit"
✅ "Welke Git commando's gebruik ik voor branching?"

### Nieuwe documenten toevoegen

Plaats gewoon nieuwe `.md`, `.txt` of `.pdf` bestanden in de `data/` folder en ze worden automatisch geïndexeerd!

## 🔧 Watcher Service Beheer

**Status checken:**
```bash
./status.sh
```

**Handmatig stoppen:**
```bash
launchctl unload ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist
```

**Handmatig starten:**
```bash
launchctl load ~/Library/LaunchAgents/com.local-mcp-kb.watcher.plist
```

**Logs bekijken:**
```bash
tail -f ~/.local-mcp-kb/watcher.log
```

## 🔧 Troubleshooting

### Tools verschijnen niet?

1. Controleer of Claude Desktop echt volledig herstart is
2. Kijk in de Claude Desktop logs:
   ```bash
   open ~/Library/Logs/Claude/
   ```

### Geen resultaten?

De database is al geïndexeerd met 136 chunks uit 18 bestanden. Als er geen resultaten komen:
1. Herstart Claude Desktop
2. Test met een simpele vraag: "Wat staat er in de Docker cheatsheet?"

### Wil je de database vernieuwen?

```bash
cd /Users/marcostalman/Projects/local-mcp-kb
.venv/bin/python src/ingestion.py
```

## 🎉 Veel plezier!

Je hebt nu je eigen lokale AI-assistent die toegang heeft tot al je documentatie. Stel gerust vragen en experimenteer!
