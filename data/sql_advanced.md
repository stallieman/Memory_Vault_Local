# 📘 SQL Reference: GROUP BY vs Window Functions vs JOIN vs Subquery vs CTE

## 🧱 1. GROUP BY – gebruik dit bij “per”-vragen

```sql
SELECT 
    maand,
    SUM(verkoop_bedrag) AS totaal_per_maand
FROM 
    verkopen
GROUP BY 
    maand;
```

🔍 **Uitleg:**  
Gebruik `GROUP BY` om data te groeperen per categorie, zoals per maand, per klant, per product. Deze query telt verkoopbedragen per maand op.

---

## 🪟 2. Window Function – behoudt originele rijen, voegt kolom toe

```sql
SELECT 
    maand,
    verkoper_id,
    verkoop_bedrag,
    AVG(verkoop_bedrag) OVER (PARTITION BY maand) AS gemiddeld_per_maand
FROM 
    verkopen;
```

🔍 **Uitleg:**  
Geeft per rij het gemiddelde van alle verkoopbedragen in die maand, zonder de rijen te groeperen. `OVER (PARTITION BY ...)` deelt de data op per maand.

---

## 🧠 3. Window Function + GROUP BY combineren

```sql
SELECT 
    maand,
    SUM(verkoop_bedrag) AS totaal_per_maand,
    AVG(verkoop_bedrag) OVER (PARTITION BY maand) AS gemiddeld_per_maand
FROM 
    verkopen
GROUP BY 
    maand;
```

🔍 **Uitleg:**  
Combineert totalen per maand (GROUP BY) met het gemiddelde per maand (windowfunctie). Handig voor rapportages met zowel samenvattingen als gemiddelden.

---

## 🔗 4. JOIN – combineer meerdere tabellen

```sql
SELECT 
    v.verkoper_id,
    v.verkoop_bedrag,
    k.verkoper_naam
FROM 
    verkopen v
JOIN 
    verkopers k
ON 
    v.verkoper_id = k.verkoper_id;
```

🔍 **Uitleg:**  
Verbindt twee tabellen met elkaar via een sleutel. Hier koppelen we verkoper-IDs aan hun namen.

---

## 🔍 5. Subquery – voor eenmalige tussenberekening

```sql
SELECT 
    verkoper_id,
    verkoop_bedrag
FROM 
    verkopen
WHERE 
    verkoop_bedrag > (
        SELECT 
            AVG(verkoop_bedrag)
        FROM 
            verkopen
    );
```

🔍 **Uitleg:**  
Deze subquery berekent het gemiddelde verkoopbedrag. De hoofdquery toont alleen rijen die daarboven liggen.

---

## 🧩 6. CTE – voor leesbaarheid en hergebruik

```sql
WITH GemiddeldeVerkopen AS (
    SELECT 
        AVG(verkoop_bedrag) AS gemiddeld_bedrag
    FROM 
        verkopen
)
SELECT 
    verkoper_id,
    verkoop_bedrag
FROM 
    verkopen, GemiddeldeVerkopen
WHERE 
    verkoop_bedrag > gemiddeld_bedrag;
```

🔍 **Uitleg:**  
Een CTE (`WITH`) is als een tijdelijke tabel die je in de volgende query gebruikt. Goed voor structuur en overzicht.

---

## 🧠 7. Gecombineerd voorbeeld: CTE + JOIN + filter

```sql
WITH GemiddeldeVerkoop AS (
    SELECT 
        AVG(verkoop_bedrag) AS gemiddeld_bedrag
    FROM 
        verkopen
)
SELECT 
    v.verkoper_id,
    v.verkoop_bedrag,
    k.verkoper_naam
FROM 
    verkopen v
JOIN 
    verkopers k ON v.verkoper_id = k.verkoper_id
JOIN 
    GemiddeldeVerkoop g ON v.verkoop_bedrag > g.gemiddeld_bedrag;
```

🔍 **Uitleg:**  
Deze query toont alle verkopers waarvan de verkoop hoger ligt dan het gemiddelde, met hun naam erbij. Alles netjes in één overzicht.

---

## ✅ Beslisregels (samenvatting)

| Gebruik       | Wanneer                                                                 |
|---------------|-------------------------------------------------------------------------|
| `GROUP BY`    | Als je iets wilt samenvatten per kolom (per maand, per product, etc.)   |
| `JOIN`        | Als je meerdere tabellen aan elkaar wilt koppelen via een sleutel       |
| `Window Func` | Als je een berekening over meerdere rijen wilt doen, zonder te groeperen|
| `Subquery`    | Als je een tussenresultaat nodig hebt in een WHERE of SELECT            |
| `CTE`         | Als je overzichtelijke, herbruikbare tussenstappen wilt maken           |

---

## ℹ️ Wanneer kies je wat? (+ korte voorbeelden)
- **Totalen per groep** → `GROUP BY`: omzet per maand.  
  ```sql
  SELECT month, SUM(amount) AS total FROM sales GROUP BY month;
  ```
- **Vergelijk binnen groep** → Window: verkoop per verkoper + maandgemiddelde in dezelfde rijen.  
  ```sql
  SELECT seller, month, amount,
         AVG(amount) OVER(PARTITION BY month) AS avg_month
  FROM sales;
  ```
- **Top N per groep** → Window + CTE: top 3 producten per klant.  
  ```sql
  WITH ranked AS (
    SELECT customer, product, SUM(amount) AS total,
           ROW_NUMBER() OVER(PARTITION BY customer ORDER BY SUM(amount) DESC) AS rn
    FROM sales
    GROUP BY customer, product
  )
  SELECT * FROM ranked WHERE rn <= 3;
  ```
- **Herbruikbaar tussenresultaat** → CTE in plaats van subquery voor leesbaarheid.  
- **Eenmalig filter op aggregaat** → Subquery in WHERE: verkopen boven overall gemiddelde.  
  ```sql
  SELECT * FROM sales
  WHERE amount > (SELECT AVG(amount) FROM sales);
  ```
- **Combineer tabellen** → JOIN: dim/tabellen koppelen. LEFT JOIN als je basisrijen wilt behouden.  
