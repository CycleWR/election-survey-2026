#!/usr/bin/env python3
"""Writes sample-data/responses.csv: FAKE candidate responses in the same shape as the
survey spreadsheet, for developing the site. Not real candidates or answers."""
import csv, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "config/survey.json").read_text())
cols = cfg["candidateColumns"]
questions = [q for t in cfg["topics"] for q in t["questions"]]
random.seed(2026)

WARDS = {"Kitchener": 10, "Waterloo": 7, "Cambridge": 8, "Wilmot": 4, "Woolwich": 3, "Wellesley": 4}
REGIONAL = {"Kitchener", "Waterloo", "Cambridge"}
ANSWER = ("Sample answer. A real candidate's full written response appears here exactly as "
          "submitted.\n\nLine breaks between paragraphs are kept.")

races = []
for muni, n in WARDS.items():
    races.append((muni, "Mayor", ""))
    if muni in REGIONAL:
        races.append((muni, "Regional Councillor", ""))
    races += [(muni, "Councillor", f"Ward {w}") for w in range(1, n + 1)]

header = [cols["name"], "Email", cols["municipality"], cols["office"], cols["ward"], cols["website"]]
for q in questions:
    header.append(q["column"])
    if q.get("commentColumn"):
        header.append(q["commentColumn"])

rows, k = [], 0
for muni, office, ward in races:
    for _ in range(random.randint(2, 4)):
        k += 1
        row = {cols["name"]: f"Sample Candidate {k}", "Email": f"private{k}@example.com",
               cols["municipality"]: muni, cols["office"]: office, cols["ward"]: ward,
               cols["website"]: "https://example.com" if random.random() > .5 else ""}
        if random.random() > .2:  # otherwise a non-responder: listed with no answers
            for q in questions:
                if q["type"] == "choice":
                    row[q["column"]] = random.choice(q["choices"])
                    row[q["commentColumn"]] = ANSWER if random.random() > .5 else ""
                elif random.random() > .1:
                    row[q["column"]] = ANSWER
        rows.append(row)

out = ROOT / "sample-data/responses.csv"
out.parent.mkdir(exist_ok=True)
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} fake rows to {out.relative_to(ROOT)}")
