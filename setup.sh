#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v git >/dev/null || { echo 'Install Git first.' >&2; exit 1; }
if [[ "${1:-}" == "--local-python" ]]; then
  python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
  [[ -x .venv/bin/python ]] || python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements-dev.txt -e .
  .venv/bin/python scripts/init_env.py
  .venv/bin/python -m pytest -q
  echo 'Run: ./run.sh --local-python'
else
  command -v docker >/dev/null || { echo 'Install Docker Engine/Desktop with Compose v2.' >&2; exit 1; }
  docker info --format '{{.ServerVersion}}'
  docker compose version
  docker run --rm --user "$(id -u):$(id -g)" --mount "type=bind,source=$PWD,target=/workspace" -w /workspace python:3.12-slim python scripts/init_env.py
  docker compose config --quiet
  docker compose build
  echo 'Run: ./run.sh'
fi
