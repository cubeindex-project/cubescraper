#!/bin/bash

export PYTHONPATH=src
.venv/bin/python3 -m cubescraper.price_tracker.main "$@"
