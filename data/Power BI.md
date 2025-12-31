# Power BI Cheatsheet (praktisch + voorbeelden)

## Data laden
- **Get Data → SQL Server**: kies import of DirectQuery. Voorbeeld: Server `srv`, Database `sales`, Mode `Import`.
- **Get Data → Parquet/CSV uit OneLake/ADLS**: gebruik `Path` + (optioneel) SAS/cred; voor grote data liever **Direct Lake** (Fabric) of **DirectQuery**.
- **Parameters**: in Power Query `Manage Parameters` voor server/omgeving; gebruik in query’s voor dev/prod switch.

## Power Query (M) basics
- **Filteren**: kolomfilter in UI → genereert `Table.SelectRows`. Handig voor datavermindering.
- **Kolommen toevoegen**: `Add Column → Custom` (M-expressie). Voorbeeld: `if [Amount] > 1000 then "High" else "Low"`.
- **Merge/Join**: `Home → Merge Queries` → kies `Left Join` om basisdata te behouden; vergelijkbaar met SQL `JOIN`.
- **Append**: tabellen stapelen (UNION). Gebruik voor maandbestanden.
- **Remove Errors/Duplicates**: `Remove Rows` opties voor schonere data.

## Datamodel & relaties
- Stermodel: **Fact** (getallen, FK’s) + **Dims** (beschrijvend, unieke sleutel).
- Relatie richting: meestal van Dim → Fact (single). Zet op `Both` alleen bij gerichte needs.
- Markeer datums als **Date Table** (Model view) voor time-intelligence.

## DAX veelgebruikte formules (met context)
- **Totaal**: `Total Sales = SUM(FactSales[Amount])`
- **Filterde som**: `High Value Sales = CALCULATE([Total Sales], FactSales[Amount] > 1000)`
- **Distinct count**: `# Customers = DISTINCTCOUNT(FactSales[CustomerID])`
- **YoY**: `Sales YoY = CALCULATE([Total Sales], DATEADD('DimDate'[Date], -1, YEAR))`
- **Running total**: `RT Sales = CALCULATE([Total Sales], FILTER(ALL('DimDate'), 'DimDate'[Date] <= MAX('DimDate'[Date])))`
- **Switch labels**: `Segment = SWITCH(TRUE(), [Total Sales] > 1_000_000, "Enterprise", [Total Sales] > 100_000, "Mid", "SMB")`

## Visual tips
- Gebruik **Slicers** op dimensies; vermijd slicers op fact-kolommen.
- Gebruik **Field parameters** om gebruikers velden/metrics te laten wisselen.
- **Tooltip pages** voor detail on hover; activeer bij visuals.

## Performance quick wins
- Kies **Import** voor snelheid; **DirectQuery** alleen als data niet te verplaatsen is (let op latency/joins).
- Verwijder ongebruikte kolommen/rijen in Power Query → kleiner model.
- Vermijd calculated columns in DAX als het in Power Query kan (kolom is statisch → sneller load).
- Gebruik `SUMX/FILTER` spaarzaam; prefer measures met aggregaties op kolommen.
- Meet performance met **Performance Analyzer** in Desktop.

## Publicatie & refresh
- Publiceer naar de juiste workspace; configureer **Gateway** voor on-prem bronnen.
- **Scheduled refresh** instellen (max 8x/dag Pro, vaker in Premium/Fabric).
- **Incremental refresh** op datumkolom om alleen nieuwe rijen te laden.

## Veelvoorkomende taken (+ hoe)
- **Relatie maken**: Model view → sleep keys of gebruik `Manage relationships` → kies cardinality/direction.
- **Column from examples**: Power Query → Add Column → Column from Examples voor snelle parsing.
- **Duplicate pagina**: rechterklik op tab → Duplicate voor variant van visual.
- **Drillthrough**: maak aparte pagina met filter op dimensie, zet `Drillthrough` veld in paneel.

## Troubleshooting
- **Blanco relaties**: check sleutelkolom op lege waarden en duplicates. Gebruik `REMOVEFILTERS` in measures om kruiselkaar te testen.
- **DirectQuery traag**: beperk kolommen/rijen, gebruik aggregaties of composite model (Import + DQ). Controleer query folding in Power Query.
- **Refresh errors**: check Gateway credentials, privacylevels, timeouts.

## Snelle toetsen
- **Ctrl+Z/Y** undo/redo, **Ctrl+Shift+L** toggelt field list, **F11** fullscreen visual, **Alt+Shift+B** create bookmark.
