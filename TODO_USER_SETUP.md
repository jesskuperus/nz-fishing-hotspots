# TODO: optional manual setup

**Nothing here is required.** The engine and map run end to end right now on
synthetic ocean and seabed data. Each item below swaps one synthetic source
for a real one. Do them in the order listed — the first two give the biggest
jump in accuracy for the least effort.

Every value goes in `.env` (already created for you from `.env.example`).

---

## 1. Real sea surface temperature + currents — Open-Meteo (5 min, free)

No account or key needed, so this is already switched on
(`USE_LIVE_OCEAN_DATA=true`). It only falls back to synthetic data when the
network blocks it.

- This sandbox blocks the API (HTTP 403 from the outbound proxy), so every
  run here logged `Live ocean fetch failed (403 Forbidden); falling back to
  synthetic`. On your own machine it should just work.
- Verify it worked: run `./run.sh engine` and check `sources.ocean` in the
  output. Live data reads `open-meteo-marine+synthetic-mesoscale`.
- Free tier is 10,000 calls/day. Each run makes `LIVE_SAMPLE_POINTS²` calls
  (25 by default), so a daily run is nowhere near the limit.

**Why the field is still part synthetic:** Open-Meteo's marine grid is far
coarser than 500 m, so the real data sets the large-scale temperature and the
synthetic generator supplies the fine mesoscale texture the front detector
needs. Item 2 is what removes that compromise.

## 2. True front-resolving SST — Copernicus Marine (~20 min, free)

Copernicus publishes ~1 km satellite SST, which resolves real thermal fronts.

1. Register free at <https://data.marine.copernicus.eu/register>.
2. Put your login in `.env`:
   ```
   COPERNICUS_USERNAME=your_username
   COPERNICUS_PASSWORD=your_password
   COPERNICUS_DATASET_ID=SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001
   ```
3. Install the client: `.venv/bin/pip install copernicusmarine`

**Status: stubbed, not finished.** `backend/data_ingestion/ocean_fetcher.py`
detects the credentials and the package, then hands off to the next source
with a log line — the authenticated subset call still needs writing
(`_fetch_copernicus`). Setting the credentials alone will not change your
output. Flagging this plainly rather than letting it look done.

## 3. Real bathymetry — LINZ or GEBCO (~15 min, free)

The synthetic seabed is a *model* of the Tutukaka shelf, not a survey. It has
the right shape (10 m inshore, a break to 200 m+, pinnacles at the Poor
Knights) but the pinnacle positions are approximate and the depths are not
chart-accurate. **Do not navigate on it.**

- **GEBCO** (easiest, global, ~450 m): <https://download.gebco.net> — draw the
  box lat −35.80/−35.30, lon 174.30/174.90, download GeoTIFF.
- **LINZ** (better, NZ-specific): <https://data.linz.govt.nz> — search
  "bathymetry", pick a Northland depth raster or contour set, export GeoTIFF
  in EPSG:4326 or NZTM.

Then either drop the file into `data/bathymetry/` (the first raster found is
used automatically), or set `LINZ_BATHYMETRY_FILE=/path/to/file.tif`.

Negative-down elevation rasters are flipped to positive depth automatically,
non-WGS84 projections are reprojected, and holes in coverage are patched with
the synthetic surface so the slope calculation stays continuous. If a raster
covers less than 25% of the bounding box it is rejected with a warning.

Needs `rasterio`, which `./run.sh setup` installs if a wheel is available.

## 4. Mapbox GL basemap (optional, ~5 min, free tier)

The UI ships with free Esri Ocean + CARTO dark tiles and needs no token. If
you want Mapbox's bathymetric styling instead, get a public token at
<https://account.mapbox.com> and set `MAPBOX_TOKEN=pk.…`. The `/api/v1/config`
endpoint already passes it to the frontend; the Mapbox GL renderer itself
isn't wired up yet (the Leaflet one is).

---

## Calibration — the item worth your actual time

The score weights (0.4 / 0.4 / 0.2) come from the spec, and the normalisation
ceilings in `backend/config.py` are my estimates of what each field reaches on
this coast, not fitted values:

| Setting | Default | Means |
|---|---|---|
| `TEMP_GRADIENT_CEILING_C_PER_KM` | 0.8 | a 0.8 °C/km front scores full marks |
| `SLOPE_CEILING_DEG` | 6.0 | 6° of seabed slope scores full marks |
| `CURRENT_CEILING_MS` | 0.7 | 0.7 m/s scores full marks |
| `DEPTH_MIN/MAX_FISHABLE_M` | 12 / 250 | outside this band the score tapers |

**Unverified: none of this has been validated against actual catch data.**
Until it is, treat the map as "here is where the structure and the water
change", not a catch prediction. Logging where you actually caught fish and
comparing against that day's grid is the only thing that turns this into a
predictor.

## 5. Real bathymetry, automatically (~2 min, free)

```bash
python scripts/fetch_bathymetry.py
.venv/bin/pip install rasterio
```

Downloads GEBCO 2024 (~450 m global grid, no account) into
`data/bathymetry/`, where the loader picks it up on the next run.

**Unverified:** this sandbox blocks the GEBCO endpoint (HTTP 403 from the
outbound proxy), so the download path has never actually completed here. The
failure path is tested; the success path is not. If it 403s or returns an
error page, the script says so and the pipeline carries on synthetic.

## 6. Log your trips (~30 seconds per trip, free, and the one that matters)

```bash
python scripts/log_catch.py --lat -35.47 --lon 174.74 \
    --species snapper --fish 4 --hours 3
python scripts/calibrate.py
```

The score's weights have never been checked against a fish. Twenty logged
trips is the point at which `calibrate.py` will tell you whether the map is
finding anything real. Nothing else on this list changes that.
