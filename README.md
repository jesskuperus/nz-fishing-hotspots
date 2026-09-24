# NZ Marine Hotspot Predictor

Daily spatial fishing-hotspot scoring for the **Tutukaka Coast and Poor
Knights Shelf**, Northland NZ. Ingests sea surface temperature, ocean
currents and seabed bathymetry, scores a 500 m × 500 m grid 0–100, and serves
it as GeoJSON on an interactive dark nautical map.

## Run it

```bash
./run.sh            # venv + deps + tests + engine + server
```

Then open <http://localhost:8000>. `make` does the same thing.

Individual steps: `./run.sh setup | test | engine | serve` (or
`make setup test engine serve`, `PORT=9000 make serve`).

**It works immediately with no accounts, keys or downloads.** Missing
credentials and missing GIS files are not errors — every ingestion path falls
back to a synthetic generator, and the UI badges the run `SYNTHETIC DATA` so
you always know which you're looking at. See `TODO_USER_SETUP.md` to swap in
real data sources.

## How the score works

```
Hotspot Score = (temp gradient weight × 0.4)
              + (depth slope weight   × 0.4)
              + (current velocity weight × 0.2)
```

Each input is normalised 0–1 against a ceiling in `backend/config.py`, the
weighted sum is scaled to 0–100, then multiplied by a depth-band factor so
steep ground outside 12–250 m doesn't score as fishable.

- **Thermal fronts** — SST gradient via `numpy.gradient` in °C/km. Cells at or
  above **0.5 °C/km** are flagged `is_thermal_front` and outlined cyan.
- **Seabed slope** — depth gradient in degrees; finds drop-offs, pinnacles and
  canyon walls. Laplacian curvature is exported too, which is what
  distinguishes a pinnacle from a plain sloping shelf.
- **Current velocity** — speed and bearing from the u/v components.

Cells are returned ranked by score, so `?limit=20` gives you the day's best
marks. Each cell also carries `score_percentile` — its rank against the rest
of the day's water cells. That's what the map colours by, so a flat day still
reads usefully instead of rendering uniformly yellow.

## API

| Endpoint | What it does |
|---|---|
| `GET /` | the single-page map UI |
| `GET /api/v1/hotspots` | scored grid as GeoJSON |
| `GET /api/v1/top?n=20` | the day's best marks as a plain JSON list |
| `POST /api/v1/regenerate` | force a recalculation |
| `GET /api/v1/config` | bbox, weights, thresholds for the frontend |
| `GET /api/v1/health` | which data sources are configured |

`/api/v1/hotspots` takes `date` (YYYY-MM-DD), `resolution_m` (100–5000),
`min_score` (0–100), `min_percentile` (0–100), `limit`, and `refresh=true`.
Runs are cached to `data/output/` and recomputed on demand.

```bash
curl 'localhost:8000/api/v1/hotspots?min_percentile=98&limit=10' > top.geojson
curl 'localhost:8000/api/v1/top?n=5'
```

Full run at 500 m is 8,600-odd water cells, about 6 MB of GeoJSON and ~4 s
cold. Drop to `resolution_m=1000` for a quick look.

## Layout

```
├── backend/
│   ├── config.py                    # every knob, all env-overridable
│   ├── api.py                       # FastAPI: GeoJSON + UI
│   ├── data_ingestion/
│   │   ├── ocean_fetcher.py         # Open-Meteo / Copernicus + fallback
│   │   ├── mock_ocean_fetcher.py    # synthetic SST fronts + currents
│   │   ├── bathymetry_loader.py     # LINZ/GEBCO raster + fallback
│   │   ├── mock_bathymetry.py       # synthetic Tutukaka shelf + pinnacles
│   │   └── coastline.py             # land mask
│   └── engine/
│       ├── grid.py                  # 500 m grid over the bbox
│       ├── features.py              # gradients, slope, curvature
│       ├── scoring.py               # the scoring formula
│       └── pipeline.py              # ingest → score → GeoJSON
├── frontend/index.html              # the local FastAPI map
├── public/index.html                # the published phone map
├── tests/test_pipeline.py           # runs standalone or under pytest
├── run_engine.py                    # CLI: one-off run
├── build_static.py                  # regenerates public/hotspots_today.geojson
└── data/output/hotspots_today.geojson
```

## Data sources

| Layer | Live source | Fallback |
|---|---|---|
| SST + currents | Open-Meteo Marine (no key) | `mock_ocean_fetcher` |
| SST (fronts) | Copernicus Marine — **stubbed, see TODO** | `mock_ocean_fetcher` |
| Bathymetry | LINZ / GEBCO raster in `data/bathymetry/` | `mock_bathymetry` |

Set `USE_LIVE_OCEAN_DATA=false` to force synthetic data — useful offline, and
it makes runs reproducible via `RANDOM_SEED`.

## Honest limits

- **The scoring is uncalibrated.** The weights come from the spec and the
  normalisation ceilings are estimates, not values fitted to catch data.
  Nothing here has been validated against actual fish caught. Treat it as
  "where the structure and the water change", not a catch prediction.
- **The synthetic seabed is a model, not a survey.** Pinnacle positions are
  approximate and depths are not chart-accurate. **Do not navigate on it.**
  Load a real raster before trusting a depth.
- Copernicus ingestion is detected but not implemented — credentials alone
  won't change your output.
- Open-Meteo's marine grid is much coarser than 500 m, so on a live run the
  real data sets the large-scale field and the synthetic generator supplies
  the fine texture. `sources.ocean` in the metadata says exactly what you got.

## Tests

```bash
./run.sh test        # or: .venv/bin/python tests/test_pipeline.py
```

10 checks covering grid sizing, the SST range, front detection, the land
mask, depth span, score bounds and ranking, GeoJSON wellformedness, the
scoring formula itself, offline fallback, and the GeoDataFrame export.

## On your phone

`public/index.html` is a static, mobile-first version of the map that needs
no server: it reads `hotspots_today.geojson` from the same directory. Deploy
this repo to Vercel (no build step — `vercel.json` just publishes `public/`)
and the map is live at your domain's root. Add it to your home screen and it
opens like an app.

- `.github/workflows/hotspots-daily.yml` regenerates the grid at 05:30 NZST
  each morning and commits it, which triggers a Vercel redeploy. Run it on
  demand from the Actions tab (**Daily hotspot grid → Run workflow**).
- Rebuild it locally with `python build_static.py`.
- The payload is the full 500 m grid: ~6 MB on disk, ~640 KB gzipped over
  the wire. A 1 km grid would be a quarter the size but smears the thermal
  fronts below the 0.5 °C/km threshold, so it stays at 500 m.
- Leaflet is vendored at `public/vendor/`, so the map still opens with one
  bar of signal. Basemap tiles still need a connection; the scored grid
  itself renders without one once the page is cached.

**Note:** committing a ~6 MB file daily grows the repo by roughly 2 GB a
year. If that starts to bite, switch the workflow to push the GeoJSON to a
single-commit orphan branch (or object storage) and point `DATA_URL` in
`hotspots.html` at it.

## When to go, not just where

The map answers *where*. Tide, daylight, moon and weather answer *when* — and
they are scored separately on purpose. A rising tide lifts every cell on the
map by the same amount, so folding it into the cell score would inflate the
numbers without ever changing which mark ranks first.

| Layer | Where it lands | Why |
| --- | --- | --- |
| Temp gradient, seabed slope, current | Cell score | Varies cell to cell |
| **Chlorophyll-a** | Cell score | Varies cell to cell — a front through barren water is just a line |
| **Tide movement, daylight, moon** | Hourly bite window | Same for the whole box |
| **Wind, swell** | Fishability | Doesn't move fish; stops you reaching them |

    Bite score = (tide movement x 0.50) + (light x 0.35) + (moon x 0.15)

`GET /api/v1/windows` returns the hourly timeline; the static map ships the
same block inside `metadata.timing`, so the phone needs no second request.

## Chlorophyll in the score

The formula is now:

    Hotspot Score = (temp gradient x 0.40) + (depth slope x 0.40)
                  + (current x 0.20) + (chlorophyll x 0.15)
                  ... all divided by the total weight, so it stays 0-100

Chlorophyll normalises as a **band**, not "more is better": 1.0 between 0.25
and 1.20 mg/m³, falling away in barren blue water below and in murky bloom
water above. `WEIGHT_CHLOROPHYLL=0` recovers the brief's original formula
exactly.

## Calibration — the only thing that makes this accurate

Every weight here is a guess, mine or the brief's. Logging trips is what
turns that into something testable:

```bash
python scripts/log_catch.py --lat -35.47 --lon 174.74 \
    --species snapper --fish 4 --hours 3 --notes "incoming tide, 40 m"
python scripts/calibrate.py     # rank correlation, once 20+ trips are in
```

`calibrate.py` refuses to report a correlation below 20 usable trips rather
than dressing up noise as a finding.

## Better seabed data

```bash
python scripts/fetch_bathymetry.py   # GEBCO 2024, no account needed
pip install rasterio                  # so the loader can read it
```

The synthetic seabed is the weakest layer in the engine and half the score
depends on its slope. **Neither the synthetic nor GEBCO grid is a navigation
chart** — these depths are for deciding where to fish, never for deciding
where it is safe to drive a boat.
