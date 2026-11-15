"""Package the analysis tables as {rows, meta} JSON files for the dashboard."""
import json, sys
from pathlib import Path
import pandas as pd

OUT = Path(sys.argv[1]); DEST = Path(sys.argv[2]); DEST.mkdir(exist_ok=True, parents=True)
code = (Path(__file__).parent / "analysis.py").read_text()
meta = [{"label": "analysis.py", "value": code, "type": "code", "lang": "python"},
        {"label": "Input", "value": "City of Toronto Open Data - TTC Subway Delay Data (2022 to Oct 2025); cause categories from the SmartTransit project (github.com/asvath/SmartTransit)"}]
r = json.load(open(OUT / "results.json"))
summary = pd.DataFrame([r["summary"]])
tables = {"summary": summary.to_dict(orient="records")}
for name in ["yoy_jan_oct", "category", "codes_top20", "stations_top10", "hours", "monthly"]:
    tables[name] = pd.read_csv(OUT / f"{name}.csv").to_dict(orient="records")
for name, rows in tables.items():
    json.dump({"rows": rows, "meta": meta}, open(DEST / f"{name}.json", "w"))
    print(name, len(rows))
