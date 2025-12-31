```sql
-- ==============================
-- Basic SELECT Statements
-- ==============================

-- Basic SELECT example
SELECT column1, column2
FROM table_name;

-- Select all columns
SELECT * FROM table_name;

-- SELECT with WHERE Clause
SELECT column1, column2
FROM table_name
WHERE condition;

-- Example:
SELECT first_name, last_name
FROM employees
WHERE department = 'Sales';

-- SELECT with ORDER BY Clause
SELECT column1, column2
FROM table_name
ORDER BY column1 ASC, column2 DESC;

-- Example:
SELECT first_name, last_name, hire_date
FROM employees
ORDER BY hire_date DESC;

-- SELECT with GROUP BY and HAVING
SELECT column, aggregate_function(column)
FROM table_name
GROUP BY column
HAVING aggregate_function(column) condition;

-- Example:
SELECT department, COUNT(*) AS num_employees
FROM employees
GROUP BY department
HAVING COUNT(*) > 10;

-- Aggregate Functions
SELECT COUNT(*) AS total_rows,
       SUM(salary) AS total_salary,
       AVG(salary) AS average_salary,
       MIN(salary) AS min_salary,
       MAX(salary) AS max_salary
FROM employees;

-- ==============================
-- JOINs
-- ==============================

-- INNER JOIN
SELECT a.column1, b.column2
FROM table_a AS a
INNER JOIN table_b AS b
    ON a.common_field = b.common_field;

-- Example:
SELECT e.first_name, e.last_name, d.department_name
FROM employees AS e
INNER JOIN departments AS d
    ON e.department_id = d.id;

-- LEFT JOIN
SELECT a.column1, b.column2
FROM table_a AS a
LEFT JOIN table_b AS b
    ON a.common_field = b.common_field;

-- Example:
SELECT e.first_name, e.last_name, d.department_name
FROM employees AS e
LEFT JOIN departments AS d
    ON e.department_id = d.id;

-- RIGHT JOIN
SELECT a.column1, b.column2
FROM table_a AS a
RIGHT JOIN table_b AS b
    ON a.common_field = b.common_field;

-- Example:
SELECT e.first_name, e.last_name, d.department_name
FROM employees AS e
RIGHT JOIN departments AS d
    ON e.department_id = d.id;

-- FULL OUTER JOIN
SELECT a.column1, b.column2
FROM table_a AS a
FULL OUTER JOIN table_b AS b
    ON a.common_field = b.common_field;

-- Example:
SELECT e.first_name, e.last_name, d.department_name
FROM employees AS e
FULL OUTER JOIN departments AS d
    ON e.department_id = d.id;

-- ==============================
-- Subqueries
-- ==============================

SELECT column1
FROM table_name
WHERE column2 = (
    SELECT column2
    FROM another_table
    WHERE condition
);

-- Example:
SELECT first_name, last_name
FROM employees
WHERE department_id = (
    SELECT id
    FROM departments
    WHERE department_name = 'Engineering'
);

-- ==============================
-- Window Functions
-- ==============================

SELECT column1,
       aggregate_function(column2) OVER (
           PARTITION BY column3
           ORDER BY column4
       ) AS window_result
FROM table_name;

-- Example:
SELECT first_name, last_name, salary,
       RANK() OVER (ORDER BY salary DESC) AS salary_rank
FROM employees;

-- ==============================
-- Common Table Expressions (CTE)
-- ==============================

WITH cte_name AS (
    SELECT column1, column2
    FROM table_name
    WHERE condition
)
SELECT *
FROM cte_name
WHERE additional_condition;

-- Example:
WITH HighEarners AS (
    SELECT first_name, last_name, salary
    FROM employees
    WHERE salary > 100000
)
SELECT first_name, last_name
FROM HighEarners
ORDER BY salary DESC;

-- ==============================
-- Set Operations
-- ==============================

-- UNION (removes duplicates)
SELECT column1 FROM table_a
UNION
SELECT column1 FROM table_b;

-- UNION ALL (includes duplicates)
SELECT column1 FROM table_a
UNION ALL
SELECT column1 FROM table_b;

-- INTERSECT
SELECT column1 FROM table_a
INTERSECT
SELECT column1 FROM table_b;

-- EXCEPT
SELECT column1 FROM table_a
EXCEPT
SELECT column1 FROM table_b;

-- ==============================
-- LIMIT and OFFSET
-- ==============================

SELECT column1, column2
FROM table_name
LIMIT 10 OFFSET 5;

-- ==============================
-- TOP Clause (SQL Server)
-- ==============================

SELECT TOP 10 column1, column2
FROM table_name;

-- ==============================
-- DISTINCT Keyword
-- ==============================

SELECT DISTINCT column1
FROM table_name;

-- ==============================
-- CASE Statements
-- ==============================

SELECT column1,
       CASE
           WHEN condition1 THEN 'Result1'
           WHEN condition2 THEN 'Result2'
           ELSE 'Other'
       END AS new_column
FROM table_name;

-- Example:
SELECT first_name, salary,
       CASE
           WHEN salary >= 100000 THEN 'High'
           WHEN salary >= 50000 THEN 'Medium'
           ELSE 'Low'
       END AS salary_category
FROM employees;

-- ==============================
-- Derived Tables
-- ==============================

SELECT a.column1, b.derived_column
FROM table_a AS a
JOIN (
    SELECT column2 AS derived_column, foreign_key
    FROM table_b
) AS b
    ON a.id = b.foreign_key;

-- ==============================
-- Pivot and Unpivot (SQL Server)
-- ==============================

-- Pivot example
SELECT *
FROM (
    SELECT Year, Quarter, Revenue
    FROM Sales
) AS SourceTable
PIVOT (
    SUM(Revenue)
    FOR Quarter IN ([Q1], [Q2], [Q3], [Q4])
) AS PivotTable;

-- Unpivot example
SELECT Year, Quarter, Revenue
FROM (
    SELECT Year, [Q1], [Q2], [Q3], [Q4]
    FROM Sales
) AS Pivoted
UNPIVOT (
    Revenue FOR Quarter IN ([Q1], [Q2], [Q3], [Q4])
) AS UnpivotTable;

-- ==============================
-- SQL Server Stored Procedure Example
-- ==============================

CREATE PROCEDURE GetEmployeesByDepartment
    @DepartmentName NVARCHAR(50)
AS
BEGIN
    SELECT e.first_name, e.last_name, d.department_name
    FROM employees AS e
    INNER JOIN departments AS d
        ON e.department_id = d.id
    WHERE d.department_name = @DepartmentName;
END;
GO

-- ==============================
-- MySQL Stored Procedure Example
-- ==============================

DELIMITER //
CREATE PROCEDURE GetEmployeesByDepartment (IN deptName VARCHAR(50))
BEGIN
    SELECT e.first_name, e.last_name, d.department_name
    FROM employees AS e
    INNER JOIN departments AS d
        ON e.department_id = d.id
    WHERE d.department_name = deptName;
END //
DELIMITER ;

-- ==============================
-- PostgreSQL-Specific Examples
-- ==============================

CREATE EXTENSION IF NOT EXISTS tablefunc;

-- Type Conversion
SELECT CAST('123' AS INTEGER);
SELECT '123'::INTEGER;

-- String Functions
SELECT LEFT('PostgreSQL', 4);
SELECT SUBSTRING('PostgreSQL' FROM 5 FOR 6);
SELECT UPPER('postgresql');
SELECT LENGTH('PostgreSQL');
SELECT CONCAT('Post','gre','SQL');

-- ==============================
-- PostgreSQL Function Example
-- ==============================

CREATE OR REPLACE FUNCTION get_employees_by_department(dept_name VARCHAR)
RETURNS TABLE(first_name VARCHAR, last_name VARCHAR, department_name VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT e.first_name, e.last_name, d.department_name
    FROM employees e
    INNER JOIN departments d ON e.department_id = d.id
    WHERE d.department_name = dept_name;
END;
$$ LANGUAGE plpgsql;

-- ==============================
-- Practice Database Creation Script
-- ==============================

CREATE DATABASE practice_db;

-- Customers
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50)
);

-- (Other tables… full script omitted for brevity in this summary)
```
~~~markdown

---

## ℹ️ Wanneer gebruik je welke SQL-patronen? (+ voorbeeld)
- **SELECT + WHERE** → filteren op ruwe data. Voorbeeld: actieve klanten: `WHERE status='active'`.
- **ORDER BY** → sorteren voor rapport/paginatie. Voorbeeld: `ORDER BY created_at DESC LIMIT 50`.
- **GROUP BY + HAVING** → samenvatten per categorie en daarna filteren op resultaat. Voorbeeld: `HAVING COUNT(*) > 10` voor drukke klanten.
- **JOIN** → data uit meerdere tabellen samenvoegen. Voorbeeld: `JOIN orders o ON o.customer_id = c.id`.
- **LEFT JOIN** → basis + optionele data (je wilt basisrijen behouden). Voorbeeld: klanten zonder orders tonen.
- **CTE** → leesbare tussenstappen of filteren op window-resultaat. Voorbeeld: top 3 per klant met `ROW_NUMBER` in een CTE.
- **Window functions** → rankings/rollen zonder rijen te reduceren. Voorbeeld: `ROW_NUMBER() OVER(PARTITION BY customer ORDER BY total DESC)`.
- **UNION vs UNION ALL** → resultaten stapelen (distinct vs alles). Voorbeeld: combineer actieve en historische tabellen.
- **LIMIT/OFFSET** → paginatie; bij grote tabellen liever keyset pagination.  
- **CASE** → conditie-gedreven labels. Voorbeeld: salarisbanden of statuslabels.
