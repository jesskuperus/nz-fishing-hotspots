# Marine reserve patch (nz-fishing-hotspots)

Copy `files/` over the repo root (same paths). `reserves-code.patch` shows the edits to public/index.html and backend/engine/pipeline.py. New files: backend/engine/reserves.py, data/marine_reserves.geojson, public/marine_reserves.geojson, tests/test_reserves.py.

What it does
- Removes any scored cell touching a DOC marine reserve (plus ~110 m margin) in the engine, so the daily GeoJSON never ranks them.
- Phone map also filters the loaded grid client-side (so a stale file can't show reserve marks), re-ranks, and refuses to show marks if the boundary file fails to load.
- "Reserves" toggle (default ON) draws the reserves as red dashed no-take zones with a tooltip. Turning it off hides the outline only; marks inside stay suppressed.
- The smoothed heat layer no longer paints colour over removed cells.

Boundaries: DOC Marine Reserves FeatureServer, queried for the Tutukaka bbox: Poor Knights Islands and Whangarei Harbour. Refresh from
https://services1.arcgis.com/3JjYDyG3oajxU6HO/arcgis/rest/services/DOC_Marine_Reserves/FeatureServer/0

Requires shapely (already in requirements.txt). Run `python tests/test_reserves.py`. Not run here (no repo checkout/engine env); frontend verified in headless Chrome against the live grid.
