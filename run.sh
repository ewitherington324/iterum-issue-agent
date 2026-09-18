#!/usr/bin/env bash
# Start the Iterum Issue Resolution Agent prototype.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f .env ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "No .env file and no ANTHROPIC_API_KEY in the environment."
  echo "  cp .env.example .env   and put your key in it."
  exit 1
fi

if [ ! -f data/taxonomy.json ]; then
  .venv/bin/python data/extract_taxonomy.py
fi

echo "Iterum Issue Resolution Agent -> http://localhost:8000"
exec .venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000 --log-level warning
