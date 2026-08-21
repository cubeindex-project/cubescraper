#!/bin/bash

export PYTHONPATH=src
.venv/bin/uvicorn cubescraper.app:app --host 0.0.0.0 --port 8000
