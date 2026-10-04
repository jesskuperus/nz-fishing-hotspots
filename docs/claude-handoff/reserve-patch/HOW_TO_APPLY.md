# Applying the reserve patch
Files in this folder: reserves.py -> backend/engine/reserves.py; test_reserves.py -> tests/test_reserves.py; marine_reserves.geojson -> data/marine_reserves.geojson AND public/marine_reserves.geojson.
reserves-code.patch is a diff for public/index.html and backend/engine/pipeline.py. Try `git apply --check docs/claude-handoff/reserve-patch/reserves-code.patch` from the repo root; if it does not apply cleanly (repo moved on), apply the edits by hand from the diff. The full patched index.html and pipeline.py are in Drive (reserve-patch.zip, folder "Fishing app") if needed.
After applying: run the tests, then check the map at 375px and 1280px with Reserves on and off. No mark may sit inside a reserve.
