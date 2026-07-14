#!/bin/bash
export PYTHONPATH=src

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

.venv/bin/pip install -r requirements.txt
