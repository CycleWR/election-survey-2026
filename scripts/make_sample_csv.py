#!/usr/bin/env python3
"""Writes sample-data/responses.csv: FAKE candidate responses with the same columns, in the
same order, as the survey spreadsheet. Not real candidates or answers.

To load it into the Google Sheet: File > Import > Upload > "Replace current sheet"."""
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
for city, n in WARDS.items():
    races.append((city, "Mayor"))
    if city in REGIONAL:
        races.append((city, "Regional Councillor"))
    races += [(city, f"Ward Councillor - Ward {w}") for w in range(1, n + 1)]

# Form metadata and private columns come first in the sheet; they are never published.
header = ["Submission ID", "Respondent ID", "Submitted at", cols["name"], "Your email address",
          "unique_token", cols["municipality"], cols["office"]]
for q in questions:
    header.append(q["column"])
    if q.get("commentColumn"):
        header.append(q["commentColumn"])

rows, k = [], 0
for city, position in races:
    for _ in range(random.randint(2, 4)):
        k += 1
        row = {"Submission ID": f"sample{k:04d}", "Respondent ID": f"resp{k:04d}",
               "Submitted at": f"2026-09-{random.randint(1, 25):02d} 12:00:00",
               cols["name"]: f"Sample Candidate {k}", "Your email address": f"private{k}@example.com",
               "unique_token": f"token{k:04d}", cols["municipality"]: city, cols["office"]: position}
        if random.random() > .2:  # otherwise a non-responder: listed with no answers
            for q in questions:
                if q.get("municipalities") and city.lower() not in q["municipalities"]:
                    continue
                if q["type"] == "choice":
                    row[q["column"]] = random.choice(q["choices"])
                    if q.get("commentColumn"):
                        row[q["commentColumn"]] = ANSWER if random.random() > .5 else ""
                elif random.random() > .1:
                    row[q["column"]] = ANSWER
        rows.append(row)

out = ROOT / "sample-data/responses.csv"
out.parent.mkdir(exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=header)
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} fake rows to {out.relative_to(ROOT)}")
