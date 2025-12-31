# 🧠 Pandas – Filtering, .loc en Toewijzing + Schoonmaak Essentials (uitgebreid)

## 🧹 Basisworkflow Data Cleaning
1. **Inlezen**
```python
import pandas as pd
df = pd.read_csv("bestand.csv", dtype=str, na_values=["", "NA", "N/A", None])
```
- `dtype=str` → eerst als tekst (veilig inspecteren)  
- `na_values` → wat telt als leeg  

2. **Verkennen**
```python
df.shape           # (rijen, kolommen)
df.info()          # types + non-null
df.head(3)         # eerste regels
df.sample(5)       # willekeurige steekproef
df.describe()      # numeriek overzicht
df.isna().sum()    # nulls per kolom
```

3. **Duplicaten**
```python
df.duplicated().sum()
df = df.drop_duplicates(subset=['id'], keep='first')
```

4. **Tekst opschonen**
```python
df['Name'] = df['Name'].str.strip()
df['City'] = df['City'].str.lower()
df['Postal'] = df['Postal'].str.replace(" ", "", regex=False)
df['Phone'] = df['Phone'].str.replace(r"\D+", "", regex=True)
df['FullName'] = df['FullName'].str.split("(", n=1).str[0]
```

5. **Types corrigeren**
```python
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Category'] = df['Category'].astype('category')
```

6. **Missende waarden vullen**
```python
df['Score'] = df['Score'].fillna(0)
df['Price'] = df['Price'].fillna(df['Price'].median())
df['Status'] = df['Status'].fillna('onbekend')
```

7. **Outliers & regels**
```python
df = df[df['Price'].between(0, 10000)]
low, high = df['Score'].quantile([0.01, 0.99])
df = df[df['Score'].between(low, high)]
```

---

## 🧩 Extra schoonmaak uit Ryan & Matt (cricket-dataset)
**Numerieke kolommen opschonen vóór casten**
```python
df['Highest_Score'] = df['Highest_Score'].str.split('*', n=1).str[0]
df['Highest_Score'] = pd.to_numeric(df['Highest_Score'], errors='coerce')

df['Balls_Faced'] = df['Balls_Faced'].str.split('+', n=1).str[0]
df['Balls_Faced'] = pd.to_numeric(df['Balls_Faced'], errors='coerce')
```

**Datum-achtige velden splitsen**
```python
df[['Start_Year', 'End_Year']] = df['Span'].str.split('-', n=1, expand=True)
df['Start_Year'] = pd.to_numeric(df['Start_Year'], errors='coerce')
df['End_Year'] = pd.to_numeric(df['End_Year'], errors='coerce')
df['Career_Length'] = df['End_Year'] - df['Start_Year']
```

**Player + Country scheiden**
```python
df['Country'] = df['Player'].str.extract(r'\(([^)]+)\)')
df['Player'] = df['Player'].str.replace(r'\s*\([^)]*\)', '', regex=True).str.strip()
```

**Aanbevolen volgorde**  
Inspect → Missings → Symbolen/spaties → Splitsen → Types → Duplicaten-check

---

## 🔍 Filters en booleans
- `df['Kolom'] == waarde` → True/False per rij  
- Combineer met `&` (EN), `|` (OF), `~` (NIET). Altijd haakjes.

```python
df[(df['Age'] > 30) & (df['City'] == 'Amsterdam')]
```

---

## 📍 Eén methode: `.loc`
`df.loc[ <filter>, <kolommen> ]`
```python
# Selectie
df.loc[df['Age'] > 30]

# Selectie + kolommen
df.loc[df['Age'] > 30, ['Name', 'City']]

# Waarden aanpassen (veilig, geen SettingWithCopy)
df.loc[df['City'] == 'Amsterdam', 'Age'] = df['Age'].mean()
```

---

## ⚙️ Toewijzing
- Zonder `=` → alleen kijken  
- Met `=` → schrijven in DataFrame
```python
df['Balls_Faced'] = df['Balls_Faced'].fillna(0)
```

---

## 📦 Samenvatting (cheatsheet)
| Actie | Patroon | Resultaat |
|---|---|---|
| Filter | `df.loc[cond]` | subset rijen |
| Kolommen | `df.loc[:, ['k1','k2']]` | subset kolommen |
| Schrijven | `df.loc[cond, 'kol'] = waarde` | inplace update |
| Dubbels | `df.drop_duplicates(subset=['k'])` | unieke rijen |
| Strip/lower | `df['k'].str.strip().str.lower()` | tekst netjes |
| Numeriek | `pd.to_numeric(..., errors='coerce')` | tekst→getal |
| Datum | `pd.to_datetime(..., errors='coerce')` | tekst→datum |
| Split | `df['k'].str.split('-', expand=True)` | kolommen splitsen |
| Regex extract | `df['k'].str.extract(r'...')` | patroon vangen |

---

## ℹ️ Wanneer gebruik je wat? (+ korte voorbeelden)
- **Nulls tellen**: `df.isna().sum()` → bepalen welke kolommen schoonmaak nodig hebben.  
- **Duplicaten droppen**: `df.drop_duplicates(subset=['id'])` → sleutel uniek houden.  
- **Tekst strip/lower**: `df['city'] = df['city'].str.strip().str.lower()` → join/groupby robuuster.  
- **Regex schoonmaak**: `df['phone'] = df['phone'].str.replace(r"\\D+", "", regex=True)` → alleen cijfers.  
- **Types casten**: `pd.to_numeric(df['price'], errors='coerce')` → klaar voor som/avg; slechte waarden → NaN.  
- **Filter + toewijzing**: `df.loc[df['score'] < 0, 'score'] = 0` → negatieve scores clampen.  
- **GroupBy**: `df.groupby('country')['amount'].sum()` → totalen per land; combineer met `.reset_index()`.  
- **Datetime features**: `df['date'] = pd.to_datetime(df['date']); df['year'] = df['date'].dt.year` → bruikbaar voor tijd-analyses.  

---

## 🧯 End-to-end template (met uitlegregels)
Dit is een “praktisch startscript” dat je telkens kunt hergebruiken. Ik heb korte toelichting per blok toegevoegd en kleine valkuilen gerepareerd (zoals de ontbrekende `numpy`-import en voorzichtig omgaan met `inplace`).

```python
import pandas as pd
import numpy as np  # nodig voor np.number in select_dtypes

# 1) Load data (pas pad/extensie aan)
data = pd.read_csv('your_dataset.csv')        # of:
# data = pd.read_excel('your_dataset.xlsx')

# 2) Inspectie (structuur en inhoud)
print(data.shape)                # (rows, cols)
print(data.columns.tolist())     # kolomnamen
print(data.head())               # eerste rijen
print(data.info())               # dtypes + nulls

# 3) Kolomnamen normaliseren (consistent snake_case)
data.columns = [col.strip().lower().replace(" ", "_") for col in data.columns]

# 4) Datatypes converteren (robust, met errors='coerce')
#    - datumkolommen: ongeldige waarden → NaT (zoals NaN voor datetime)
data['date_column'] = pd.to_datetime(data['date_column'], errors='coerce')

#    - numerieke kolommen: ongeldige waarden → NaN
numeric_cols = ['numeric_column1', 'numeric_column2']
for col in numeric_cols:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

#    - categorische kolommen (zuiniger geheugen, sneller groupby)
category_cols = ['category_column']
for col in category_cols:
    if col in data.columns:
        data[col] = data[col].astype('category')

# 5) Duplicaten en missende waarden
#    Duplicaten: kies subset als je een sleutel hebt; anders hele rij
data = data.drop_duplicates()

#    Missende waarden:
#    - numeriek: mean/median (kies wat semantisch klopt)
for col in data.select_dtypes(include=[np.number]).columns:
    if data[col].isna().any():
        data[col] = data[col].fillna(data[col].mean())

#    - niet-numeriek: mode (meest voorkomende waarde)
for col in data.select_dtypes(exclude=[np.number]).columns:
    if data[col].isna().any():
        mode = data[col].mode(dropna=True)
        if not mode.empty:
            data[col] = data[col].fillna(mode[0])

# 6) Feature engineering (optioneel, voorbeeld)
if 'existing_feature' in data.columns:
    data['new_feature'] = data['existing_feature'] * 2

# 7) Samenvatting & controle
print(data.describe())               # numeriek
print(data.describe(include='all'))  # alles (kan traag bij veel tekst)
print(data.isnull().sum())           # resterende nulls

# 8) Correlatie (alleen numeriek)
num_cols = data.select_dtypes(include=[np.number]).columns
corr_matrix = data[num_cols].corr()
print(corr_matrix)

# 9) Opslaan van verwerkte data
data.to_csv('processed_dataset.csv', index=False)
```

**Uitleg bij keuzes in het template**
- **Kolomnamen normaliseren** → voorkomt later typfouten en rommel met spaties/hoofdletters.  
- **`errors='coerce'`** → maakt conversies voorspelbaar: rommel → NaN/NaT, daarna kun je bewust vullen of filteren.  
- **Vullen met `mean`/`mode`** → is een *startpunt*; kies per veld iets dat semantisch klopt (soms median, soms letterlijk leeg laten).  
- **`drop_duplicates()`** zonder subset → voorzichtig; beter is een natuurlijke sleutel (bijv. `['id','date']`).  
- **Geen `inplace=True`** → expliciete toewijzing (`data = ...`) is duidelijker en vermijdt copy-waarschuwingen.

---

## 🧩 Mini-voorbeeld (blijft handig om gevoel te houden)
```python
import pandas as pd

df = pd.DataFrame({
    'Name': ['Jan', 'Piet', 'Klaas'],
    'Age': [25, None, 41],
    'City': ['Rotterdam', 'Amsterdam', 'Utrecht']
})

# Filter: alleen rijen waar Age ontbreekt
print(df.loc[df['Age'].isna()])

# Toewijzing: vul NaN in Age met gemiddelde
df.loc[df['Age'].isna(), 'Age'] = df['Age'].mean()
print(df)

# Filter en kolommen samen
print(df.loc[df['Age'] > 30, ['Name', 'City']])
```
