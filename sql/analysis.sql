-- TTC Subway Delay Analysis: SQL version (DuckDB / PostgreSQL-compatible)
-- Author: Reezwan-Us Sami
-- Input: data/ttc_subway_delays_clean_2022_2025.csv (produced by src/analysis.py)
-- Run:   duckdb -c ".read sql/analysis.sql"

CREATE OR REPLACE TABLE delays AS
SELECT * FROM read_csv_auto('data/ttc_subway_delays_clean_2022_2025.csv');

-- Focus window used throughout: Jan 2023 - Oct 2025
CREATE OR REPLACE VIEW focus AS
SELECT * FROM delays WHERE date >= DATE '2023-01-01';

-- 1. Headline KPIs
SELECT
    COUNT(*)                                             AS incidents,
    COUNT(*) FILTER (WHERE min_delay > 0)                AS delay_incidents,
    SUM(min_delay)                                       AS delay_minutes,
    ROUND(SUM(min_delay) / 60.0)                         AS delay_hours,
    ROUND(100.0 * COUNT(*) FILTER (WHERE min_delay > 0) / COUNT(*), 1) AS pct_causing_delay
FROM focus;

-- 2. Year over year, January-October only (data ends 2025-10-31)
SELECT
    YEAR(date)                                           AS year,
    COUNT(*)                                             AS incidents,
    COUNT(*) FILTER (WHERE min_delay > 0)                AS delay_incidents,
    SUM(min_delay)                                       AS delay_minutes
FROM delays
WHERE MONTH(date) <= 10
GROUP BY 1
ORDER BY 1;

-- 3. Delay minutes by cause category, with share of total
SELECT
    category,
    SUM(min_delay)                                       AS delay_minutes,
    COUNT(*)                                             AS delay_incidents,
    ROUND(100.0 * SUM(min_delay) / SUM(SUM(min_delay)) OVER (), 1) AS share_pct
FROM focus
WHERE min_delay > 0
GROUP BY 1
ORDER BY delay_minutes DESC;

-- 4. Pareto of delay codes: cumulative share of delay minutes
WITH by_code AS (
    SELECT code, description, category,
           SUM(min_delay) AS delay_minutes,
           COUNT(*)       AS delay_incidents,
           MEDIAN(min_delay) AS median_min
    FROM focus
    WHERE min_delay > 0
    GROUP BY 1, 2, 3
)
SELECT *,
       ROUND(100.0 * SUM(delay_minutes) OVER (ORDER BY delay_minutes DESC
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(delay_minutes) OVER (), 1) AS cum_share_pct
FROM by_code
ORDER BY delay_minutes DESC
LIMIT 25;

-- 5. Top 10 stations by delay minutes
SELECT station_clean AS station,
       SUM(min_delay) AS delay_minutes,
       COUNT(*)       AS delay_incidents
FROM focus
WHERE min_delay > 0
GROUP BY 1
ORDER BY delay_minutes DESC
LIMIT 10;

-- 6. Long delays (30+ minutes): share of incidents vs share of minutes
SELECT
    ROUND(100.0 * COUNT(*) FILTER (WHERE min_delay >= 30) / COUNT(*), 1)                 AS pct_of_incidents,
    ROUND(100.0 * SUM(min_delay) FILTER (WHERE min_delay >= 30) / SUM(min_delay), 1)     AS pct_of_minutes
FROM focus
WHERE min_delay > 0;

-- 7. "No trouble found" alarms: minutes lost to alarms where nothing was wrong
SELECT description,
       SUM(min_delay) AS delay_minutes,
       COUNT(*)       AS delay_incidents
FROM focus
WHERE min_delay > 0 AND description ILIKE '%no trouble found%'
GROUP BY 1
ORDER BY delay_minutes DESC;

-- 8. Hour-of-day profile
SELECT hour, SUM(min_delay) AS delay_minutes, COUNT(*) AS delay_incidents
FROM focus
WHERE min_delay > 0
GROUP BY 1
ORDER BY 1;
