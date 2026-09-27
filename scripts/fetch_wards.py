#!/usr/bin/env python3
"""Downloads ward boundaries from the Region of Waterloo open data portal and writes
data/wards.geojson. Run by the "Update data" GitHub Action (needs internet access).

    python3 scripts/fetch_wards.py
"""
import json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = "https://rowopendata-rmw.opendata.arcgis.com"
SOURCES = [  # municipality id, display name, ArcGIS Hub item id
    ("waterloo", "Waterloo", "026226d6f7de4c47a9b034fed186b78e"),
    ("kitchener", "Kitchener", "aaa70fb878304de4ba244f12c5447016"),
]
# Property names that hold the ward number in municipal datasets, most likely first.
WARD_FIELDS = ["WARD", "WARD_ID", "WARD_NO", "WARD_NUM", "WARDNUMBER", "WARD_NUMBER", "WARDID", "WARD_NAME", "NAME", "LABEL"]


def download(item):
    urls = [f"{HUB}/api/download/v1/items/{item}/geojson?layers=0",
            f"https://opendata.arcgis.com/datasets/{item}_0.geojson"]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cyclewr-survey"})
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:  # try the next URL
            print(f"  {url}: {e}", file=sys.stderr)
    sys.exit(f"Could not download item {item}")


def ward_number(props):
    upper = {k.upper(): v for k, v in props.items()}
    for field in WARD_FIELDS:
        v = upper.get(field)
        m = re.search(r"\d+", str(v)) if v is not None else None
        if m:
            return int(m.group())
    sys.exit(f"No ward number field found in properties: {list(props)}")


def round_coords(c):
    return [round_coords(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]


features = []
for muni, name, item in SOURCES:
    print(f"Downloading {name} wards…")
    for f in download(item)["features"]:
        n = ward_number(f["properties"])
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
        features.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "race": f"{muni}-ward-{n}", "municipality": muni, "ward": n, "name": f"{name} Ward {n}"}})
    print(f"  {sum(1 for f in features if f['properties']['municipality'] == muni)} wards")

(ROOT / "data/wards.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}) + "\n")
