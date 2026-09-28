#!/usr/bin/env python3
"""Builds the site's data/*.json from the survey spreadsheet.

    python3 scripts/build_data.py responses.csv [more.csv ...]   # downloaded CSV(s), e.g. one per tab
    python3 scripts/build_data.py --sheet                        # fetch the sheet tabs in config/survey.json

Only the columns named in config/survey.json are published; everything else in
the sheet (emails, phone numbers, notes) is ignored. Races are derived from the
candidate rows, so add a row (name + race, no answers) for candidates who did
not respond.
"""
import csv, io, json, re, sys
from pathlib import Path

from sheets import fetch_tab_csv

ROOT = Path(__file__).resolve().parent.parent
OFFICE_ORDER = ["Regional Chair", "Mayor", "Regional Councillor", "Ward Councillor"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in reader]
    return [h.strip() for h in reader.fieldnames or []], rows, text


def read_tabs(cfg, sources):
    """Yields (label, header, rows, raw text) for each sheet tab (--sheet) or local CSV file."""
    if sources == ["--sheet"]:
        s = cfg["sheet"]
        for tab in s["tabs"]:
            yield (f"tab '{tab['name']}'", *parse_csv(fetch_tab_csv(s["id"], tab["gid"])))
    else:
        for path in sources:
            yield (path, *parse_csv(Path(path).read_text(encoding="utf-8-sig")))


def parse_race(text, municipalities):
    """Turns free-form race text ('Kitchener', 'City Councillor', 'Ward 3') into a race."""
    t = text.lower()
    muni = next((m for m in municipalities if m["id"] != "region" and m["name"].lower() in t), None)
    ward = re.search(r"ward\D{0,3}(\d+)", t) or re.search(r"\b(\d{1,2})\b", t)
    if "chair" in t:
        office, muni = "Regional Chair", next(m for m in municipalities if m["id"] == "region")
    elif re.search(r"\bregion", t):  # "Regional Councillor", or just "Region"
        office = "Regional Councillor"
    elif "mayor" in t:
        office = "Mayor"
    elif ward:
        office = "Ward Councillor"
    else:
        return None
    if not muni:
        return None
    if office == "Regional Chair":
        return {"id": "region-chair", "municipality": "region", "office": office, "name": "Regional Chair"}
    if office == "Ward Councillor":
        n = int(ward.group(1))
        return {"id": f"{muni['id']}-ward-{n}", "municipality": muni["id"], "office": office,
                "ward": n, "name": f"{muni['name']} Ward {n} Councillor"}
    suffix = "mayor" if office == "Mayor" else "regional-councillor"
    name = f"{muni['name']} Mayor" if office == "Mayor" else f"Regional Councillor ({muni['name']})"
    return {"id": f"{muni['id']}-{suffix}", "municipality": muni["id"], "office": office, "name": name}


def normalise_choice(value, choices):
    for c in choices:
        if value.lower() == c.lower():
            return c
    return value  # publish unexpected answers as written rather than dropping them


def main(sources):
    cfg = json.loads((ROOT / "config/survey.json").read_text())
    cols, munis = cfg["candidateColumns"], cfg["municipalities"]
    wanted = [cols["name"]] + [q[k] for t in cfg["topics"] for q in t["questions"]
                               for k in ("column", "commentColumn") if q.get(k)]
    rows = []
    for label, header, tab_rows, raw in read_tabs(cfg, sources):
        missing = [c for c in wanted if c not in header]
        if missing:
            sys.exit(f"Columns not found in {label} (check config/survey.json):\n  " + "\n  ".join(missing)
                     + f"\n\n{label} has columns:\n  " + "\n  ".join(repr(h) for h in header)
                     + "\n\nFirst rows, as downloaded:\n" + "\n".join(raw.splitlines()[:15]))
        rows += [(label, i, r) for i, r in enumerate(tab_rows, start=2)]

    races, candidates, problems, seen = {}, [], [], {}
    for label, i, row in rows:
        name = row.get(cols["name"], "")
        if not name:
            continue
        race_text = " ".join(row.get(cols[k], "") for k in ("municipality", "office", "ward") if cols.get(k))
        race = parse_race(race_text, munis)
        if not race:
            problems.append(f"{label} row {i} ({name}): can't tell which race from '{race_text}'")
            continue
        races[race["id"]] = race

        answers = {}
        for t in cfg["topics"]:
            for q in t["questions"]:
                value = row.get(q["column"], "")
                comment = row.get(q["commentColumn"], "") if q.get("commentColumn") else ""
                a = {}
                if q["type"] == "choice" and value:
                    a["choice"] = normalise_choice(value, q.get("choices", []))
                elif value:
                    comment = f"{value}\n\n{comment}".strip()
                if comment:
                    a["comment"] = comment
                if a:
                    answers[q["id"]] = a

        cid = slug(name)
        if cid in seen:  # same name twice, e.g. a resubmission: keep the later row
            candidates.remove(seen[cid])
            problems.append(f"{label} row {i} ({name}): duplicate name, keeping this later row")
        c = {"id": cid, "name": name, "race": race["id"],
             "website": row.get(cols.get("website", ""), ""),
             "responded": bool(answers), "answers": answers}
        seen[cid] = c
        candidates.append(c)

    if not candidates:  # never publish an empty site because the sheet is empty or was cleared
        print("No candidate rows in the sheet; keeping the current data.")
        return

    muni_order = [m["id"] for m in munis]
    race_list = sorted(races.values(), key=lambda r: (
        muni_order.index(r["municipality"]), OFFICE_ORDER.index(r["office"]), r.get("ward", 0)))
    survey = {"title": cfg["title"], "topics": [
        {**{k: v for k, v in t.items() if k != "questions"},
         "questions": [{k: v for k, v in q.items() if k not in ("column", "commentColumn")} for q in t["questions"]]}
        for t in cfg["topics"]]}

    used = {r["municipality"] for r in race_list}
    write("data/survey.json", survey)
    write("data/races.json", {"municipalities": [m for m in munis if m["id"] in used], "races": race_list})
    write("data/candidates.json", candidates)
    print(f"{len(candidates)} candidates ({sum(c['responded'] for c in candidates)} responded) in {len(race_list)} races")
    for p in problems:
        print("WARNING:", p)


def write(path, obj):
    (ROOT / path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
