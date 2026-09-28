#!/usr/bin/env python3
"""Prints the tabs of a public Google Sheet with each tab's header and first rows, to help
map a new sheet layout in config/survey.json. Email/token values are hidden.

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
    private = {i for i, h in enumerate(header) if re.search(r"email|token|phone", h, re.I)}
    data = [r for r in rows[1:] if any(c.strip() for c in r)]
    print(f"\n===== TAB {name!r} gid={gid}: {len(data)} non-empty rows =====")
    for i, h in enumerate(header):
        print(f"  col {i}: {h!r}")
    for r in data[:3]:
        print("  ROW:", [("<hidden>" if i in private and c else c[:80]) for i, c in enumerate(r)])
