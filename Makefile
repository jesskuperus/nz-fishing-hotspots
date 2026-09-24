VENV := .venv
PY := $(VENV)/bin/python
PORT ?= 8000

.PHONY: all setup engine serve test clean
all: setup test engine serve   ## set up, verify, score today, serve

setup:        ## create the venv and install dependencies
	./run.sh setup

engine:       ## run the spatial engine once, writing hotspots_today.geojson
	./run.sh engine

serve:        ## launch the API + map UI on http://localhost:$(PORT)
	PORT=$(PORT) ./run.sh serve

test:         ## verify the pipeline end to end on synthetic data
	./run.sh test

clean:        ## remove generated GeoJSON and caches
	rm -rf data/output/*.geojson
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
