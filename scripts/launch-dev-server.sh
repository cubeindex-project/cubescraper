#!/bin/bash

export PYTHONPATH=src
.venv/bin/uvicorn cubescraper.app:app --host 127.0.0.1 --port 8000 --reload
