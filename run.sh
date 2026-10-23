#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-8098}"
exec python3 -m uvicorn rush.app:app --host 0.0.0.0 --port "$PORT"
