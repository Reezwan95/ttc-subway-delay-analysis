"""
TTC Subway Delay Analysis (Jan 2022 - Oct 2025)
Author: Reezwan-Us Sami

Cleans the City of Toronto / TTC subway delay open data, then builds the
KPI tables behind the dashboard and the recommendations memo.

Usage:  python src/analysis.py <raw_delays_dir> <delay_codes_csv> <out_dir>
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

RAW, CODES, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- load
frames = []
for year in (2022, 2023, 2024):
    frames.append(pd.read_excel(RAW / f"ttc-subway-delay-data-{year}.xlsx"))
frames.append(pd.read_excel(RAW / "TTC Subway Delay Data since 2025.xlsx").drop(columns="_id"))
df = pd.concat(frames, ignore_index=True)
raw_rows = len(df)

# ---------------------------------------------------------------- clean
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
df["date"] = pd.to_datetime(df["date"])
df["hour"] = pd.to_datetime(df["time"].astype(str).str[:5], format="%H:%M", errors="coerce").dt.hour
df["code"] = df["code"].fillna("").astype(str).str.strip().str.upper()
df["line_raw"] = df["line"].fillna("").astype(str).str.strip().str.upper()


def norm_line(s: str) -> str:
    s = s.replace("LINE", "").replace(" ", "")
    if s in ("YU", "YUS", "1"):
        return "Line 1 (YU)"
    if s in ("BD", "2"):
        return "Line 2 (BD)"
    if s in ("SHP", "SHEP", "4"):
        return "Line 4 (SHP)"
    if s in ("SRT", "3"):
        return "Line 3 (SRT)"
    if "YU" in s and "BD" in s:
        return "Lines 1 & 2"
    return "Other/Unknown"


df["line_clean"] = df["line_raw"].map(norm_line)


def norm_station(s) -> str:
    s = "" if pd.isna(s) else str(s).upper().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b(STATION|STN|STA)\b\.?", "", s)
    s = re.sub(r"\((TO|APPROACHING|LEAVING).*?\)", "", s)
    s = re.sub(r"\s+(BD|YU|YUS|SHP|LINE \d)$", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


df["station_clean"] = df["station"].map(norm_station)

codes = pd.read_csv(CODES, encoding="cp1252")
codes["CODE"] = codes["CODE"].str.strip().str.upper()
df = df.merge(codes[["CODE", "DESCRIPTION", "Category"]], left_on="code", right_on="CODE", how="left")
df["category"] = df["Category"].fillna("Unknown").replace({"Weather/External": "Weather"})
df["description"] = df["DESCRIPTION"].fillna("Unmapped code").str.strip().str.title()

# Scope: the three operating lines (Line 3 SRT closed in July 2023) plus shared-line rows.
scope = df[df["line_clean"].isin(["Line 1 (YU)", "Line 2 (BD)", "Line 4 (SHP)", "Lines 1 & 2"])].copy()
scope["delayed"] = scope["min_delay"] > 0
scope["year"] = scope["date"].dt.year
scope["month"] = scope["date"].dt.to_period("M").astype(str)

clean_cols = ["date", "hour", "day", "station_clean", "line_clean", "code", "description",
              "category", "min_delay", "min_gap", "bound", "vehicle"]
scope[clean_cols].to_csv(OUT / "ttc_subway_delays_clean_2022_2025.csv", index=False)

# ---------------------------------------------------------------- KPIs
# Comparable window: January-October of each year (data ends 2025-10-31).
jo = scope[scope["date"].dt.month <= 10]
yoy = (jo.groupby("year")
       .agg(incidents=("code", "size"),
            delay_incidents=("delayed", "sum"),
            delay_minutes=("min_delay", "sum"))
       .reset_index())
yoy["avg_min_per_delay"] = (yoy["delay_minutes"] / yoy["delay_incidents"]).round(2)
yoy["pct_incidents_causing_delay"] = (100 * yoy["delay_incidents"] / yoy["incidents"]).round(1)

# Focus window for the deep-dive: Jan 2023 - Oct 2025 (34 months).
f = scope[scope["date"] >= "2023-01-01"]
d = f[f["delayed"]]
total_min = d["min_delay"].sum()

cat = (d.groupby("category")["min_delay"].agg(["sum", "size"]).rename(columns={"sum": "delay_minutes", "size": "delay_incidents"})
       .sort_values("delay_minutes", ascending=False).reset_index())
cat["share_pct"] = (100 * cat["delay_minutes"] / total_min).round(1)

codes_rank = (d.groupby(["code", "description", "category"])["min_delay"].agg(["sum", "size", "median"])
              .rename(columns={"sum": "delay_minutes", "size": "delay_incidents", "median": "median_min"})
              .sort_values("delay_minutes", ascending=False).reset_index())
codes_rank["cum_share_pct"] = (100 * codes_rank["delay_minutes"].cumsum() / total_min).round(1)
n_codes_80 = int((codes_rank["cum_share_pct"] < 80).sum() + 1)

stations = (d.groupby("station_clean")["min_delay"].agg(["sum", "size"])
            .rename(columns={"sum": "delay_minutes", "size": "delay_incidents"})
            .sort_values("delay_minutes", ascending=False).reset_index())
top_stations = stations.head(10).copy()
top10_station_share = round(100 * top_stations["delay_minutes"].sum() / total_min, 1)

hours = (d.groupby("hour")["min_delay"].agg(["sum", "size"])
         .rename(columns={"sum": "delay_minutes", "size": "delay_incidents"}).reset_index())

lines = (d.groupby("line_clean")["min_delay"].agg(["sum", "size", "median"])
         .rename(columns={"sum": "delay_minutes", "size": "delay_incidents", "median": "median_min"})
         .sort_values("delay_minutes", ascending=False).reset_index())

monthly = (f.groupby("month").agg(delay_minutes=("min_delay", "sum"), delay_incidents=("delayed", "sum")).reset_index())

long = d[d["min_delay"] >= 30]
long_share_incidents = round(100 * len(long) / len(d), 1)
long_share_minutes = round(100 * long["min_delay"].sum() / total_min, 1)

patron = d[d["category"] == "Patron"]
patron_top = (patron.groupby("description")["min_delay"].agg(["sum", "size"])
              .rename(columns={"sum": "delay_minutes", "size": "delay_incidents"})
              .sort_values("delay_minutes", ascending=False).head(5).reset_index())

summary = {
    "raw_rows": int(raw_rows),
    "rows_in_scope": int(len(scope)),
    "focus_window": "2023-01-01 to 2025-10-31",
    "focus_incidents": int(len(f)),
    "focus_delay_incidents": int(len(d)),
    "focus_delay_minutes": int(total_min),
    "focus_delay_hours": round(total_min / 60),
    "median_delay_min": float(d["min_delay"].median()),
    "pct_incidents_causing_delay": round(100 * len(d) / len(f), 1),
    "n_codes_total": int(codes_rank.shape[0]),
    "n_codes_for_80pct": n_codes_80,
    "top10_station_share_pct": top10_station_share,
    "long_delay_share_incidents_pct": long_share_incidents,
    "long_delay_share_minutes_pct": long_share_minutes,
    "unmapped_code_share_pct": round(100 * d.loc[d["description"] == "Unmapped Code", "min_delay"].sum() / total_min, 1),
}

tables = {
    "yoy_jan_oct": yoy, "category": cat, "codes_top20": codes_rank.head(20),
    "stations_top10": top_stations, "hours": hours, "lines": lines, "monthly": monthly,
    "patron_top5": patron_top,
}
for name, t in tables.items():
    t.to_csv(OUT / f"{name}.csv", index=False)
json.dump({"summary": summary, **{k: v.to_dict(orient="records") for k, v in tables.items()}},
          open(OUT / "results.json", "w"), indent=1, default=str)
print(json.dumps(summary, indent=1))
print(yoy.to_string())
print(cat.to_string())
print(codes_rank.head(15).to_string())
print(top_stations.to_string())
print(lines.to_string())
print(patron_top.to_string())
