#!/usr/bin/env python3
"""Prints the tabs of a Google Sheet with each tab's columns, to help map a new sheet layout in
config/survey.json. Actions logs are public, so no answers are printed: only row counts and the
distinct values of the race columns (City, Position), which are public anyway.

    python3 scripts/inspect_sheet.py SHEET_ID
"""
import csv, io, re, sys, urllib.request

from sheets import _service_account, fetch_tab_csv, list_tabs

sheet = sys.argv[1]
base = f"https://docs.google.com/spreadsheets/d/{sheet}"
get = lambda url: urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8-sig")

if _service_account()[0]:
    tabs = list_tabs(sheet)
else:  # public sheet: scrape the tab list from the read-only web view
    html = get(f"{base}/htmlview")
    tabs = re.findall(r'id="sheet-button-(\d+)"[^>]*>\s*<a[^>]*>([^<]+)</a>', html) \
        or [(g, n) for n, g in re.findall(r'name:\s*"([^"]+)"[^}]*?gid:\s*"(\d+)"', html)]
    if not tabs:
        sys.exit("Couldn't find tabs; page starts:\n" + html[:3000])

for gid, name in tabs:
    rows = list(csv.reader(io.StringIO(fetch_tab_csv(sheet, gid))))
    header = rows[0] if rows else []
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    print(f"\n===== TAB {name!r} gid={gid}: {len(data)} non-empty rows =====")
    for i, h in enumerate(header):
        print(f"  col {i}: {h!r}")
    for i, h in enumerate(header):
        if re.fullmatch(r"\s*(city|municipality|position|office|race|ward)\s*", h, re.I):
            values = sorted({r[i].strip() for r in data if i < len(r) and r[i].strip()})
            print(f"  distinct {h.strip()!r} values: {values}")
