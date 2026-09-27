#!/usr/bin/env python3
"""Downloads ward boundaries from the Region of Waterloo open data portal and writes
data/wards.geojson. Run by the "Update data" GitHub Action (needs internet access).

    python3 scripts/fetch_wards.py
"""
import json, math, re, sys, urllib.request
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
    urls = [f"{HUB}/api/download/v1/items/{item}/geojson?layers=0&spatialRefId=4326",
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


def utm17n_to_lonlat(x, y):
    """UTM zone 17N (NAD83, EPSG:26917) metres -> WGS84 lon/lat (NAD83 differs by < 2 m here)."""
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
            + (151 * e1**3 / 96) * math.sin(6 * mu) + (1097 * e1**4 / 512) * math.sin(8 * mu))
    n1 = a / math.sqrt(1 - e2 * math.sin(phi1)**2)
    t1, c1 = math.tan(phi1)**2, ep2 * math.cos(phi1)**2
    r1 = a * (1 - e2) / (1 - e2 * math.sin(phi1)**2) ** 1.5
    d = (x - 500000) / (n1 * k0)
    lat = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d**3 / 6
           + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120) / math.cos(phi1)
    return math.degrees(lon) - 81, math.degrees(lat)


def to_lonlat(c):
    """Rounds to ~1 m, converting projected coordinates if the portal ignored spatialRefId."""
    if isinstance(c[0], list):
        return [to_lonlat(x) for x in c]
    x, y = c[0], c[1]
    if abs(x) > 180 or abs(y) > 90:
        x, y = utm17n_to_lonlat(x, y)
    return [round(x, 5), round(y, 5)]


features = []
for muni, name, item in SOURCES:
    print(f"Downloading {name} wards…")
    for f in download(item)["features"]:
        n = ward_number(f["properties"])
        f["geometry"]["coordinates"] = to_lonlat(f["geometry"]["coordinates"])
        features.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "race": f"{muni}-ward-{n}", "municipality": muni, "ward": n, "name": f"{name} Ward {n}"}})
    print(f"  {sum(1 for f in features if f['properties']['municipality'] == muni)} wards")

(ROOT / "data/wards.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}) + "\n")
