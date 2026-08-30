#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
[[ -f .env ]] || { echo 'Run setup.sh first.' >&2; exit 1; }
if [[ "${1:-}" == "--local-python" ]]; then
  exec .venv/bin/python -m src.api.server
else
  docker compose up --build --wait
fi
