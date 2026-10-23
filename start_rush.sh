#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
set -a; [ -f .env ] && . ./.env; set +a
exec python3 -m uvicorn rush.app:app --host 0.0.0.0 --port "${PORT:-8098}"
