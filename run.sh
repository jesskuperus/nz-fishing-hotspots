#!/usr/bin/env bash
# Set up the venv, install deps, run the engine, launch the server.
# Usage: ./run.sh [engine|serve|setup|test]   (default: everything)
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
PY="$VENV/bin/python"
PORT="${PORT:-8000}"

setup() {
  if [ ! -x "$PY" ]; then
    echo "==> Creating virtual environment"
    python3 -m venv "$VENV"
  fi
  echo "==> Installing dependencies"
  "$VENV/bin/pip" install --quiet --upgrade pip
  # rasterio/xarray are optional; don't fail the setup if wheels are missing.
  "$VENV/bin/pip" install --quiet \
    "numpy>=1.26" "scipy>=1.11" "geopandas>=1.0" "shapely>=2.0" \
    "fastapi>=0.110" "uvicorn[standard]>=0.27" "httpx>=0.27" "python-dotenv>=1.0"
  "$VENV/bin/pip" install --quiet rasterio xarray netCDF4 \
    || echo "    (optional raster libs unavailable — synthetic bathymetry still works)"
  [ -f .env ] || { cp .env.example .env; echo "==> Created .env from .env.example"; }
}

engine() {
  echo "==> Running the spatial engine"
  "$PY" run_engine.py
}

serve() {
  echo "==> Serving on http://localhost:$PORT"
  exec "$PY" -m uvicorn backend.api:app --host 0.0.0.0 --port "$PORT"
}

tests() {
  echo "==> Verifying the pipeline"
  "$PY" tests/test_pipeline.py
}

case "${1:-all}" in
  setup)  setup ;;
  engine) engine ;;
  serve)  serve ;;
  test)   tests ;;
  all)    setup; tests; engine; serve ;;
  *) echo "Usage: $0 [all|setup|engine|serve|test]"; exit 2 ;;
esac
