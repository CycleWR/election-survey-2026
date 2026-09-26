"""Generates PLACEHOLDER data so the site design can be reviewed.
Replace data/*.json and data/wards.geojson with real data before launch."""
import json, random

random.seed(7)
CITIES = {  # name: (ward count, rough bbox lon0, lat0, lon1, lat1, rows)
    "kitchener": ("Kitchener", 10, (-80.56, 43.37, -80.40, 43.445), 2),
    "waterloo":  ("Waterloo", 7,  (-80.60, 43.447, -80.49, 43.52), 2),
    "cambridge": ("Cambridge", 8, (-80.38, 43.33, -80.24, 43.43), 2),
}

features, races = [], []
races.append({"id": "region-chair", "municipality": "region", "office": "Regional Chair",
              "name": "Regional Chair"})
for slug, (name, n, (x0, y0, x1, y1), rows) in CITIES.items():
    races.append({"id": f"{slug}-mayor", "municipality": slug, "office": "Mayor", "name": f"{name} Mayor"})
    races.append({"id": f"region-{slug}", "municipality": slug, "office": "Regional Councillor",
                  "name": f"Regional Councillor ({name})"})
    per_row = [n // rows + (1 if r < n % rows else 0) for r in range(rows)]
    w = 1
    for r, count in enumerate(per_row):
        ya, yb = y0 + (y1 - y0) * r / rows, y0 + (y1 - y0) * (r + 1) / rows
        for c in range(count):
            xa, xb = x0 + (x1 - x0) * c / count, x0 + (x1 - x0) * (c + 1) / count
            rid = f"{slug}-ward-{w}"
            features.append({"type": "Feature",
                "properties": {"race": rid, "municipality": slug, "ward": w, "name": f"{name} Ward {w}"},
                "geometry": {"type": "Polygon", "coordinates": [[[xa, ya], [xb, ya], [xb, yb], [xa, yb], [xa, ya]]]}})
            races.append({"id": rid, "municipality": slug, "office": "Ward Councillor", "ward": w,
                          "name": f"{name} Ward {w} Councillor"})
            w += 1

municipalities = [{"id": "region", "name": "Region of Waterloo"}] + \
    [{"id": s, "name": v[0]} for s, v in CITIES.items()]

topics = [
    ("safety", "Safe Streets", "Vision Zero, traffic calming and speed limits"),
    ("network", "Connected Network", "Building a complete, protected cycling network"),
    ("transit", "Transit & Multi-modal Trips", "Bikes and transit working together"),
    ("maintenance", "Year-round Maintenance", "Winter clearing and upkeep of bike lanes and trails"),
    ("funding", "Funding & Priorities", "Budgets, targets and accountability"),
]
survey = {"title": "CycleWR 2026 Municipal Candidate Survey", "placeholder": True, "topics": []}
for i, (tid, title, desc) in enumerate(topics, 1):
    survey["topics"].append({"id": tid, "title": title, "description": desc, "questions": [
        {"id": f"q{i}a", "type": "choice", "choices": ["Yes", "No", "Unsure"],
         "text": f"[Placeholder] Yes/no question {i}a about {title.lower()}?"},
        {"id": f"q{i}b", "type": "open", "text": f"[Placeholder] Open-ended question {i}b about {title.lower()}."},
    ]})

LOREM = ("Placeholder answer text. The candidate's full written response will appear here, "
         "exactly as submitted, including multiple sentences where they chose to elaborate.")
candidates, k = [], 0
for race in races:
    for j in range(random.randint(2, 4)):
        k += 1
        responded = random.random() > 0.25
        c = {"id": f"candidate-{k}", "name": f"Sample Candidate {k}", "race": race["id"],
             "website": "", "responded": responded, "answers": {}}
        if responded:
            for t in survey["topics"]:
                for q in t["questions"]:
                    if q["type"] == "choice":
                        c["answers"][q["id"]] = {"choice": random.choice(q["choices"]),
                            "comment": LOREM if random.random() > .5 else ""}
                    elif random.random() > .1:
                        c["answers"][q["id"]] = {"comment": LOREM}
        candidates.append(c)

def dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2); f.write("\n")

dump("data/survey.json", survey)
dump("data/races.json", {"municipalities": municipalities, "races": races})
dump("data/candidates.json", candidates)
dump("data/wards.geojson", {"type": "FeatureCollection", "placeholder": True, "features": features})
