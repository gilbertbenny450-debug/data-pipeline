# London Food Discovery — Data Pipeline (free version)

Pulls every London food venue from OpenStreetMap, watches the food press for
buzz, flags brand-new food businesses via Companies House, takes a weekly
snapshot, and ranks venues into the three lenses from the curation spec:
**Highest Rated · Trending · Upcoming**. Runs entirely on free services.

## What it costs
Nothing. OpenStreetMap and RSS feeds need no account. Companies House needs a
free API key (no card). GitHub runs the weekly schedule free.
Ratings/velocity signals get stronger later if Google Places is added — the
code already supports it; those columns just stay empty until then.

## One-time setup (~15 minutes, no card anywhere)
1. Create a free account at github.com
2. Create a new repository (private is fine), name it e.g. `london-food-pipeline`
3. Upload everything in this folder to the repository (drag-and-drop works
   on github.com: "Add file" → "Upload files")
4. Go to the repo's **Actions** tab → enable workflows
5. Optional but recommended: get a free Companies House API key at
   developer.company-information.service.gov.uk → in the repo go to
   Settings → Secrets and variables → Actions → New repository secret →
   name `CH_API_KEY`, paste the key
6. Actions tab → "Weekly data pipeline" → **Run workflow** to do the first pull

From then on it runs itself every Monday morning and commits the updated
database (`london_food.db`) plus a readable `latest_rankings.json` to the repo.

## Files
- `run_weekly.py` — the weekly job (orchestrates everything)
- `pipeline/config.py` — every tunable threshold from the curation spec
- `pipeline/fetch_osm.py` — OpenStreetMap venue pull (the base directory)
- `pipeline/editorial.py` — food-press RSS monitoring → buzz signals
- `pipeline/companies_house.py` — new food-business detection
- `pipeline/score.py` — the three-lens ranking logic
- `pipeline/db.py` — SQLite storage, chain detection, region assignment
- `test_pipeline.py` — run `python test_pipeline.py` to verify everything
- `.github/workflows/weekly.yml` — the free Monday-morning scheduler

## Notes
- **Cold start:** venues from the very first pull are not treated as "new"
  (they were just unknown to us). Upcoming fills up from later arrivals and
  Companies House matches — expect it to be thin for the first few weeks.
- **Trending needs history:** velocity compares snapshots over time, so
  Trending becomes meaningful after 3-4 weekly runs. This is why starting
  the pipeline early matters.
- Everything follows the Curation Specification (v1.0, July 2026).
