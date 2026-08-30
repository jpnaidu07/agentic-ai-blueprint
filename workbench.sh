#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.11+ using your operating system package manager.' >&2
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt -e .
exec .venv/bin/python -m src.workbench.server --port "${1:-8080}"
