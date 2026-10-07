# CycleWR 2026 Municipal Election Survey
Results of the 2026 municipal candidate survey conducted by CycleWR.

**Live site: https://cyclewr.github.io/election-survey-2026/** (repository: `CycleWR/election-survey-2026`)

A static site (plain HTML/CSS/JS, no build step) served by GitHub Pages.

Candidate responses come from the CycleWR survey spreadsheet (see below); Kitchener and Waterloo ward
boundaries come from the Region of Waterloo open data portal.

## Pages

| Page | URL | What it shows |
|---|---|---|
| Home | `/` | Clickable ward map + directory of every race (the accessible alternative to the map) with "responded / total" counts |
| Race | `/race.html?id=kitchener-ward-3` | One race. **Browse by topic** (one tab per survey topic plus "All topics", every candidate's answer under each question, yes/no tally) or **by candidate** (all of one candidate's answers across all topics). "Also on your ballot" links to mayor / regional races. |
| Deep links | `…#topic=plan`, `…#topic=all`, `…#candidate=mohamed-askalany` | Every topic and every candidate view is shareable |
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
- `sheet.tabs` in the config lists which tabs to read (Kitchener, Waterloo, Cambridge, Townships; the "All" tab repeats them), by the
  `gid` in each tab's URL, so renaming a tab doesn't matter. Every tab must have the same columns.
- **Sheet access:** the Action reads the sheet with a Google **service account** when the repository secret
  `GOOGLE_SERVICE_ACCOUNT_KEY` is set (see below), so the sheet can stay private. Without that secret it falls
  back to the public CSV export, which needs the sheet shared as "Anyone with the link can view".
- Races are worked out from each row's municipality/position/ward text (the sheet's **City** and **Position**
  columns, e.g. `Kitchener` + `Ward 3`, `Mayor` or `Region`). To list a candidate who **did not respond**, add a row with their name and race and no answers.
- Question `type` is `"choice"` (with `choices`, shown as coloured Yes/No/Unsure chips, optional
  `commentColumn`) or `"open"` (free text).
- Wards with no candidates in the sheet yet are greyed out on the map.
- **Rides with Candidates** (optional columns): **Ride Status** (`Not requested`, `Requested` / `In progress`, or
  `Complete`), **Ride Blog Post** (link to the cyclewr.ca post) and **Ride Summary** (short text shown on the site).
  A blog post link on its own counts as Complete. Until the sheet has these columns, ride information is hidden.
- Cambridge and the townships have no boundary data, so they appear in the race list but not on the map.

Generated files (don't edit by hand): `data/survey.json`, `data/races.json`, `data/candidates.json`, `data/wards.geojson`.

If the sheet has no candidate rows, the build keeps the current data rather than publishing an empty site.

### Working with fake data

`sample-data/responses.csv` holds **fake** responses in the sheet's shape (regenerate with
`python3 scripts/make_sample_csv.py`). Its columns match the sheet's tabs, so its rows can be pasted into
them. Build the site from it with:

```sh
python3 scripts/build_data.py sample-data/responses.csv
```

### Setting up the service account

1. In the [Google Cloud console](https://console.cloud.google.com/), create (or pick) a project and enable the
   **Google Sheets API** (APIs & Services → Library).
2. IAM & Admin → **Service accounts** → Create service account (no roles needed). Open it → **Keys** →
   Add key → Create new key → **JSON**. Keep the downloaded file private and delete it once step 4 is done.
3. In the spreadsheet, **Share** it with the service account's email (`…@….iam.gserviceaccount.com`) as
   **Viewer**. You can then set General access back to "Restricted".
4. In GitHub: repository **Settings → Secrets and variables → Actions → New repository secret**, name
   `GOOGLE_SERVICE_ACCOUNT_KEY`, and paste the whole contents of the JSON file.

Run **Actions → Update data → Run workflow** to check it. Errors name the fix (e.g. which email to share with).

## Run locally

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

Leaflet 1.9.4 is vendored in `assets/vendor/leaflet` (BSD-2-Clause). Map tiles © OpenStreetMap contributors.
