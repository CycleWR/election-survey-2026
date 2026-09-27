# cyclewr-survey-2026.github.io
Results of the municipal candidate survey 2026 conducted by CycleWR.

A static site (plain HTML/CSS/JS, no build step) served by GitHub Pages.

> **Status: in development.** Questions in `config/survey.json` and candidates in `data/` are **placeholders**
> built from fake sample data; ward shapes are placeholders until the "Update data" Action first runs.

## Pages

| Page | URL | What it shows |
|---|---|---|
| Home | `/` | Clickable ward map + directory of every race (the accessible alternative to the map) with "responded / total" counts |
| Race | `/race.html?id=kitchener-ward-3` | One race. **Browse by topic** (5 topic tabs, every candidate's answer under each question, yes/no tally) or **by candidate** (all of one candidate's answers across all topics). "Also on your ballot" links to mayor / regional races. |
| Deep links | `…#topic=safety`, `…#candidate=candidate-14` | Every topic and every candidate view is shareable |
| About | `/about.html` | Methodology and the full question list |

Candidates are listed alphabetically by surname. Non-responders are shown as "Did not respond".

## How data gets onto the site

```
Google Sheet ──(GitHub Action "Update data", every 6h or on demand)──▶ scripts/build_data.py ──▶ data/*.json ──▶ site
ROW open data portal ──▶ scripts/fetch_wards.py ──▶ data/wards.geojson (Kitchener + Waterloo)
```

- **`config/survey.json`** is the one file to edit by hand. It maps each sheet column (by exact header text)
  to a topic and question, sets the question wording shown on the site, and names the candidate columns
  (name, municipality, position, ward, website). **Only columns listed there are published** — emails,
  phone numbers or notes in the sheet never reach the site.
- The sheet must be shared as **"Anyone with the link can view"** for the Action to download it.
- Races are worked out from each row's municipality/position/ward text (the sheet's **City** and **Position**
  columns, e.g. `Kitchener` + `Ward Councillor - Ward 3`, `Mayor` or `Regional Councillor`). To list a candidate who **did not respond**, add a row with their name and race and no answers.
- Question `type` is `"choice"` (with `choices`, shown as coloured Yes/No/Unsure chips, optional
  `commentColumn`) or `"open"` (free text).
- Cambridge and the townships have no boundary data, so they appear in the race list but not on the map.

Generated files (don't edit by hand): `data/survey.json`, `data/races.json`, `data/candidates.json`, `data/wards.geojson`.

If the sheet has no candidate rows, the build keeps the current data rather than publishing an empty site.

### Working with fake data

`sample-data/responses.csv` holds **fake** responses in the sheet's shape (regenerate with
`python3 scripts/make_sample_csv.py`). Its columns match the sheet exactly, so it can be loaded into the
sheet with **File → Import → Upload → Replace current sheet** (its header row is identical to the sheet's). Build the site from it with:

```sh
python3 scripts/build_data.py sample-data/responses.csv
```

## Run locally

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

Leaflet 1.9.4 is vendored in `assets/vendor/leaflet` (BSD-2-Clause). Map tiles © OpenStreetMap contributors.
