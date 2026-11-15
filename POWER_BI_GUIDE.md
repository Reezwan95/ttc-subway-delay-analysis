# Rebuilding this dashboard in Power BI (about 2–3 hours)

Recruiters for analyst roles often want to see Power BI. Build this version yourself so you can walk through every step in an interview.

## 1. Load

1. Go to **Get Data > Text/CSV** and choose `data/ttc_subway_delays_clean_2022_2025.csv`.
2. In Power Query:
   - Set `date` to Date, and `min_delay`, `min_gap` and `hour` to Whole Number.
   - Add a custom column `Delayed = if [min_delay] > 0 then 1 else 0`.
3. Create a date table with DAX: `Dates = CALENDAR(DATE(2022,1,1), DATE(2025,10,31))`, then add Year, Month and Month Name columns. Mark it as the date table and relate `Dates[Date]` to `delays[date]`.

## 2. Measures (DAX)

```DAX
Delay Minutes = SUM ( delays[min_delay] )
Delay Hours = DIVIDE ( [Delay Minutes], 60 )
Incidents = COUNTROWS ( delays )
Delaying Incidents = CALCULATE ( [Incidents], delays[min_delay] > 0 )
% Incidents Causing Delay = DIVIDE ( [Delaying Incidents], [Incidents] )
Share of Delay Minutes = DIVIDE ( [Delay Minutes], CALCULATE ( [Delay Minutes], ALL ( delays[category] ) ) )
Long Delay Minutes = CALCULATE ( [Delay Minutes], delays[min_delay] >= 30 )
% Minutes from Long Delays = DIVIDE ( [Long Delay Minutes], [Delay Minutes] )
Delay Minutes PY = CALCULATE ( [Delay Minutes], SAMEPERIODLASTYEAR ( Dates[Date] ) )
YoY % = DIVIDE ( [Delay Minutes] - [Delay Minutes PY], [Delay Minutes PY] )
```

Pareto (cumulative share by code):

```DAX
Cumulative Share =
VAR cur = [Delay Minutes]
VAR tbl = ALLSELECTED ( delays[code] )
RETURN
DIVIDE (
    SUMX ( FILTER ( tbl, [Delay Minutes] >= cur ), [Delay Minutes] ),
    CALCULATE ( [Delay Minutes], tbl )
)
```

## 3. Page layout

- **Top row:** cards for Delay Hours, Delaying Incidents, % Incidents Causing Delay, YoY % and % Minutes from Long Delays.
- **Left:** bar chart of Delay Minutes by category.
- **Right:** line-and-clustered-column chart with code on the axis, Delay Minutes as columns and Cumulative Share as the line. Show the top 20 with a Top N filter.
- **Bottom left:** line chart of Delay Minutes by month.
- **Bottom right:** column chart by hour.
- **Table:** top 10 stations.
- **Slicers:** line, year, category.

## 4. Publish

Publish to the web, or export screenshots plus the `.pbix` file to GitHub, and link both from your portfolio site.

## Check your numbers

With slicers covering Jan 2023 – Oct 2025, you should match the dashboard:
- **Delay hours:** about 3,261.
- **Customer-related share of delay minutes:** 48.7%.
- **Long delays (30+ min):** 19.9% of minutes.
