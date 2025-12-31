# End-to-End Data Project Setup

## 📁 Projectstructuur

```
/mijn_project
│── /data                # Ruwe en verwerkte data
│   └── database.db      # SQLite database
│── /notebooks           # Jupyter Notebooks voor analyses
│── /scripts             # ETL-scripts
│   └── etl.py
│── /sql                 # SQL-query’s, tabellenstructuur
│── /config              # Config (API-keys in .env)
│   └── .env
│── /tests               # Unit tests
│── main.py              # Hoofdscript om ETL te runnen
│── requirements.txt     # Python dependencies
│── README.md            # Project documentatie
│── .gitignore           # Beschermt gevoelige files
```

---

## ✅ `.gitignore`

```
config/.env
data/*.db
__pycache__/
.ipynb_checkpoints/
```

---

## 🔐 `.env` (voorbeeld)

```
API_URL="https://api.partnercenter.microsoft.com/v1/invoices"
API_KEY="YOUR_KEY_HERE"
```

---

## 📦 `requirements.txt`

```
requests
pandas
python-dotenv
sqlite3-binary
```

---

## 🔁 ETL Script – `scripts/etl.py`

```python
import os
import requests
import pandas as pd
import sqlite3
from dotenv import load_dotenv

load_dotenv("config/.env")

API_URL = os.getenv("API_URL")
DB_PATH = "data/database.db"

def extract_data():
    headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
    r = requests.get(API_URL, headers=headers)
    r.raise_for_status()
    return r.json()

def transform_data(data):
    df = pd.DataFrame(data)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

def load_data(df):
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("facturen", conn, if_exists="replace", index=False)
    conn.close()
    print("✅ Data loaded into SQLite!")

def run():
    data = extract_data()
    df = transform_data(data)
    load_data(df)

if __name__ == "__main__":
    run()
```

---

## ▶️ Hoofdscript – `main.py`

```python
from scripts.etl import run

if __name__ == "__main__":
    print("🚀 Starting ETL workflow...")
    run()
    print("🎯 Done.")
```

---

## 🧪 Testvoorbeeld – `tests/test_etl.py`

```python
from scripts.etl import transform_data

def test_transform():
    sample = [{"timestamp": "2025-01-01T10:00:00Z"}]
    df = transform_data(sample)
    assert "timestamp" in df.columns
    assert df["timestamp"].notnull().all()
```

---

## 🧠 SQL-voorbeeld – `sql/check_facts.sql`

```sql
SELECT COUNT(*) AS aantal_records
FROM facturen;
```

---

## 📓 Notebook-voorbeeld – `notebooks/analyses.ipynb`

```python
import pandas as pd
df = pd.read_sql("SELECT * FROM facturen", "sqlite:///../data/database.db")
df.head()
```

---

## 🚀 Eerste run

```bash
pip install -r requirements.txt
python main.py
```

---

## 📝 README.md (template)

```
# Mijn Data Project

Een end-to-end ETL-workflow:
• Extract: Data uit externe API
• Transform: Pandas schoonmaak
• Load: SQLite database

## Starten
pip install -r requirements.txt
python main.py
```

---

## 🔄 Mogelijke uitbreidingen

- Logging (structuur i.p.v. print)
- Dagelijkse scheduler (cron / GitHub Actions)
- Upgrade van SQLite → PostgreSQL of Fabric SQL endpoint
- Dashboard in Power BI / Fabric
- Versiebeheer van data met Delta Lake

---

## ℹ️ Hoe gebruik je dit project? (+ voorbeelden)
- **Eerste keer opzetten**: `pip install -r requirements.txt` → dependencies.  
- **Run ETL**: `python main.py` → haalt API-data op en laadt in SQLite (`data/database.db`).  
- **Test transformer**: `pytest tests/test_etl.py -q` → checkt dat `timestamp` parsed wordt.  
- **Check data** (shell): `sqlite3 data/database.db "SELECT COUNT(*) FROM facturen;"` → snelle validatie.  
- **Aanpassen bron-URL**: wijzig `API_URL` in `.env`; herstart `main.py`.  
- **Schema aanpassen**: pas `transform_data` aan (kolommen hernoemen/typen) → rerun ETL.  
```
