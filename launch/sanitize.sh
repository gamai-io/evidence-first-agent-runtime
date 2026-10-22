#!/usr/bin/env bash
# Fail if a private identifier or credential leaks into the public bundle.
# The private pattern list is intentionally NOT tracked. Put it in
# launch/.private-patterns (gitignored) or point GAMA_SANITIZE_PATTERNS at it.
set -uo pipefail
cd "$(dirname "$0")/.."

PATTERNS_FILE="${GAMA_SANITIZE_PATTERNS:-launch/.private-patterns}"
if [ ! -f "$PATTERNS_FILE" ]; then
  echo "sanitize: no pattern file ($PATTERNS_FILE); private check skipped"
  exit 0
fi

PATTERN=$(cat "$PATTERNS_FILE")
HITS=$(grep -RInE "$PATTERN" . \
  --exclude-dir=.git --exclude-dir=runs --exclude-dir=__pycache__ \
  --exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' \
  --exclude='sanitize.sh' --exclude='.private-patterns' 2>/dev/null || true)

if [ -n "$HITS" ]; then
  echo "SANITIZE FAILED — private identifiers found:"
  echo "$HITS"
  exit 1
fi
echo "sanitize: clean"
