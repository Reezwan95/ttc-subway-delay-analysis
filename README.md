# TTC Subway Delays 2023–2025: Where the Minutes Go

An operations analysis of Toronto Transit Commission subway delay data, January 2023 to October 2025, covering Lines 1, 2 and 4. I cleaned roughly 90,000 incident records, grouped 123 delay codes into cause categories, and used Pareto, time-of-day and station analysis to find where delay minutes concentrate and what could reduce them.

**Interactive charts and write-up:** [reezwan95.github.io](https://reezwan95.github.io/#work)

## Key findings

| Finding | Figure |
|---|---|
| Delay hours lost, Jan 2023 – Oct 2025 | 3,261 hours (195,635 minutes) |
| Incidents that caused a delay | 24,704 (35.4% of 69,796 logged incidents) |
| Share of delay minutes from customer-related incidents | 48.7% |
| Delay causes that account for 80% of lost minutes | 25 of 123 codes |
| Long delays (30+ min): share of incidents vs share of minutes | 2.5% of incidents, 19.9% of minutes |
| Ten stations' share of all delay minutes | 27.7% |
| Delay minutes Jan–Oct 2025 vs Jan–Oct 2024 | 58,106 vs 61,659 (−5.8%) |
| Minutes lost to alarms where no trouble was found | 14,689 (7.5%) |

The recommendations are in [`memo.md`](memo.md).

## Repository

```
├── README.md
├── memo.md                     one-page findings and recommendations
├── POWER_BI_GUIDE.md           how to rebuild the dashboard in Power BI
├── src/
│   ├── analysis.py             cleaning + KPI tables (pandas)
│   └── export_dashboard.py     packages the tables for the web dashboard
├── sql/
│   └── analysis.sql            the same analysis in SQL (DuckDB / PostgreSQL)
└── output/                     KPI tables as CSV + results.json
```

## Method

1. **Load.** Four yearly TTC subway delay files (2022 to October 2025) from the City of Toronto Open Data portal.
2. **Clean.**
   - Standardized more than 20 spellings of line names into Lines 1, 2, 4 and "Lines 1 & 2".
   - Normalized station names by removing "Station" and line suffixes.
   - Parsed times to hour of day.
   - Joined each delay code to its description and a cause category.
3. **Scope.** Line 3 (Scarborough RT), which closed in July 2023, is excluded. The deep-dive window is January 2023 to October 2025. Year-on-year comparisons use January–October of each year, because data ends on October 31, 2025.
4. **Analyze.**
   - Headline KPIs.
   - Category shares.
   - Pareto analysis of delay codes.
   - Station ranking.
   - Hour-of-day profile.
   - Long-delay concentration.
   - False-alarm ("no trouble found") minutes.
5. **Validate.** The SQL in `sql/analysis.sql` reproduces every figure from the Python pipeline independently.

## Run it

The raw yearly delay files are not stored here (about 9 MB). Download "TTC Subway Delay Data" from open.toronto.ca, then:

```bash
pip install pandas openpyxl duckdb
python src/analysis.py <folder with raw TTC .xlsx files> <delay-code category CSV> output
mkdir -p data && cp output/ttc_subway_delays_clean_2022_2025.csv data/   # created by analysis.py
duckdb -c ".read sql/analysis.sql"
```

## Limitations

- The figures are not normalized by ridership or service hours, so busier stations naturally log more incidents.
- "Min Delay" is the TTC's recorded delay to the train, not total passenger delay.
- The cause categories are a judgement-based grouping of TTC delay codes. I used the mapping published by the SmartTransit project (github.com/asvath/SmartTransit). About 14% of minutes fall under vague "other" codes.

## Data and licence

- **TTC Subway Delay Data:** City of Toronto Open Data, published under the Open Government Licence – Toronto.
- **Raw yearly files and cause-category mapping:** obtained via the SmartTransit project's public repository.

---

Reezwan-Us Sami · Industrial Engineering, University of Toronto · [LinkedIn](https://www.linkedin.com/in/reezwans)
