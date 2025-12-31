# ✅ SQL Training – Groeperen, HAVING, Window Functies, CTE's & Stored Procedures

Dit is mijn eigen *denksysteem*.  
Niet syntax onthouden, maar **zien wat de vraag wil**.

---

## 🚦 Stap 1 – Hoe ontleed ik een SQL-vraag?

Lees van links naar rechts:

1️⃣ **Wat moet ik tonen?** (SELECT-kolommen)  
2️⃣ **Per wat?** → *GROUP BY*  
3️⃣ **Welke berekening?** → *SUM / COUNT / AVG*  
4️⃣ **Wanneer filteren?**  
   - Op ruwe data? → *WHERE*  
   - Op resultáten van een berekening? → *HAVING*  
5️⃣ **Top-N? Ranking?** → *Window functie + filter → meestal CTE*

---

## 🧠 Ezelsbruggen

| Vraagzin bevat | Betekent in SQL |
|----------------|----------------|
| “per …” | GROUP BY |
| “meer dan totaal …” | HAVING |
| “top 3 / hoogste / rang” | WINDOW functie |
| filter op window result | CTE |
| “berekening op berekening” | CTE |

Kort:  
> **GROUP BY reduceert** (minder rijen)  
> **WINDOW verrijkt** (zelfde aantal rijen)  
> **CTE helpt filteren op verrijking**

---

## ✅ Oefenvragen + oplossingen

### 1️⃣ Toon alle orders van klanten uit Nederland  
*Filter op ruwe data → WHERE*

```sql
SELECT o.OrderID, c.CustomerName, o.OrderDate
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE c.Country = 'Netherlands';
```

---

### 2️⃣ Toon per klant het aantal bestellingen  
*Samenvatten per klant → GROUP BY*

```sql
SELECT c.CustomerName, COUNT(o.OrderID) AS AantalBestellingen
FROM Customers c
JOIN Orders o ON o.CustomerID = c.CustomerID
GROUP BY c.CustomerName;
```

---

### 3️⃣ Toon per klant alleen klanten met meer dan 10 bestellingen  
*Filter op aggregatie → HAVING*

```sql
SELECT c.CustomerName, COUNT(o.OrderID) AS AantalBestellingen
FROM Customers c
JOIN Orders o ON o.CustomerID = c.CustomerID
GROUP BY c.CustomerName
HAVING COUNT(o.OrderID) > 10;
```

---

### 4️⃣ Toon per klant de top 3 producten op omzet  
*Ranking binnen een groep → WINDOW + CTE*

> Mensentaal:  
> Eerst: omzet per klant-product  
> Daarna: rang per klant  
> Daarna: top 3 filteren

```sql
WITH omzet_per_klant_product AS (
  SELECT
    c.CustomerName,
    p.ProductName,
    SUM(od.Quantity * od.UnitPrice) AS TotalSales
  FROM Customers c
  JOIN Orders o        ON o.CustomerID = c.CustomerID
  JOIN OrderDetails od ON od.OrderID  = o.OrderID
  JOIN Products p      ON p.ProductID = od.ProductID
  GROUP BY c.CustomerName, p.ProductName
),
gerankt_per_klant AS (
  SELECT
    CustomerName,
    ProductName,
    TotalSales,
    ROW_NUMBER() OVER (
      PARTITION BY CustomerName
      ORDER BY TotalSales DESC
    ) AS rn
  FROM omzet_per_klant_product
)
SELECT CustomerName, ProductName, TotalSales
FROM gerankt_per_klant
WHERE rn <= 3
ORDER BY CustomerName, rn;
```

*Kort geheugenanker:*  
**TOP N in SELECT** → altijd Window.  
**TOP N filteren** → Window + CTE.

---

### 5️⃣ Toon afdelingen waarvan het gemiddelde salaris hoger is dan bedrijfs-gemiddelde  
*Aggregatie op aggregatie → CTE*

```sql
WITH gem_per_afdeling AS (
  SELECT DepartmentID, AVG(Salary) AS GemSalaris
  FROM Employees
  GROUP BY DepartmentID
),
bedrijfs_gem AS (
  SELECT AVG(GemSalaris) AS BedrijfsGemiddelde
  FROM gem_per_afdeling
)
SELECT d.DepartmentID, d.GemSalaris
FROM gem_per_afdeling d, bedrijfs_gem b
WHERE d.GemSalaris > b.BedrijfsGemiddelde;
```

---

## 🔍 Window functies – in 1 zin

| Functie | Wanneer |
|--------|---------|
| `ROW_NUMBER()` | Top N kiezen |
| `RANK()` / `DENSE_RANK()` | Top N met gelijke scores |
| `SUM() OVER()` | Totalen tonen zonder GROUP BY |
| `LAG()` / `LEAD()` | Vergelijk met vorige/volgende rij |

Regel:  
> Window = **berekenen binnen een groep, maar **alle rijen blijven staan**

---

## 🧩 CTE – wanneer?

> Als je wilt **filteren/berekenen op een resultaat dat je net hebt gemaakt**

**OVER op OVER? → knippen met CTE**  
**Top-N per groep? → window + CTE**  
**Berekening op berekening? → CTE**

Ezelsbrug:
> *Eerst ramen, dan zeven.* (window → filter)

---

## 🏗️ Stored Procedures – waarom en wanneer?

**Gebruik SP wanneer:**
- meerdere SQL-stappen **als één proces** moeten draaien
- iets **berekend én opgeslagen** moet worden
- het **herhaalbaar** is (planning, automatisering)
- **parameters** nodig zijn (bv. per periode)

**Niet gebruiken wanneer:**
- één enkele SELECT genoeg is
- het pure ad-hoc analyse is

**Voorbeeld**
```sql
CREATE PROCEDURE sp_UpdateMonthlyRevenue
AS
BEGIN
    SET NOCOUNT ON;

    DELETE FROM MonthlyCustomerRevenue;

    INSERT INTO MonthlyCustomerRevenue (CustomerID, TotalRevenue, RunDate)
    SELECT
      c.CustomerID,
      SUM(od.Quantity * od.UnitPrice),
      GETDATE()
    FROM Customers c
    JOIN Orders o        ON o.CustomerID = c.CustomerID
    JOIN OrderDetails od ON od.OrderID  = o.OrderID
    GROUP BY c.CustomerID;

    SELECT TOP 5 CustomerID, TotalRevenue
    FROM MonthlyCustomerRevenue
    ORDER BY TotalRevenue DESC;
END;
GO

-- draaien
EXEC sp_UpdateMonthlyRevenue;
```

Kort:  
> **CTE = logica binnen één query**  
> **Stored Procedure = logica over meerdere queries**

---

## ✅ Mini-beslisboom

| Ik lees… | Ik doe… |
|----------|---------|
| “per X” | GROUP BY |
| “meer dan totaal / gemiddeld” | HAVING |
| “top N / beste / hoogste” | WINDOW + CTE |
| “vergelijk binnen groep” | WINDOW |
| “eerste berekening, dan filter daarop” | CTE |
| “proces / opslag / parameters / herhaling” | Stored Procedure |

---

✅ Klaar voor gebruik in Obsidian, Neovim en WSL.  
Je hoeft dit alleen nog maar te **herlezen voor de patronen** — niet voor de syntax.

---

## ℹ️ Snelle patronen + voorbeelden
- **Left vs Inner**: toon alle klanten, ook zonder orders → `LEFT JOIN Orders o ON ... WHERE o.OrderID IS NULL` voor “zonder orders”.  
- **Top N per groep**: Window + CTE. Voorbeeld: top 2 verkopers per regio.  
  ```sql
  WITH ranked AS (
    SELECT region, seller, SUM(amount) AS total,
           ROW_NUMBER() OVER(PARTITION BY region ORDER BY SUM(amount) DESC) AS rn
    FROM sales
    GROUP BY region, seller
  )
  SELECT * FROM ranked WHERE rn <= 2;
  ```
- **Distinct vs GROUP BY**: alleen unieke waarden → `SELECT DISTINCT country FROM Customers`; met teller → `GROUP BY country` + `COUNT(*)`.  
- **HAVING**: filter op aggregaat: `HAVING SUM(amount) > 10000`.  
- **Window voor percentages**:  
  ```sql
  SELECT product,
         SUM(amount) AS total,
         SUM(amount) * 1.0 / SUM(SUM(amount)) OVER() AS pct_total
  FROM sales
  GROUP BY product;
  ```
- **CTE voor “berekening op berekening”**: eerst subtotalen, daarna filter/sort op die subtotalen.  
