#!/usr/bin/env bash
# Create public GitHub repos and push the three components.
# DRY-RUN by default. Apply only with:  ./publish-repos.sh --yes
# Requires: GH_TOKEN (repo scope), git, curl. Never prints the token.
set -euo pipefail
cd "$(dirname "$0")/.."

APPLY=0
[ "${1:-}" = "--yes" ] && APPLY=1

ORG="${ORG:-gamai-labs}"          # change to a user account if preferred
VISIBILITY="${VISIBILITY:-public}"

if [ -z "${GH_TOKEN:-}" ]; then
  echo "GH_TOKEN is not set. Create a fine-grained token with 'Administration: write'"
  echo "and 'Contents: write' for the target org, then export GH_TOKEN=... "
  exit 2
fi

./launch/sanitize.sh
./repro.sh >/dev/null

api() { curl -sS -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" "$@"; }

create_repo() {
  local name="$1" desc="$2"
  local body
  body=$(printf '{"name":"%s","description":"%s","private":false,"has_issues":true,"has_wiki":false}' "$name" "$desc")
  if [ "$APPLY" -eq 0 ]; then
    echo "[dry-run] POST /orgs/$ORG/repos  name=$name"
    return 0
  fi
  api -X POST "https://api.github.com/orgs/$ORG/repos" -d "$body" >/dev/null
  echo "created $ORG/$name"
}

push_component() {
  local dir="$1" name="$2"
  if [ "$APPLY" -eq 0 ]; then
    echo "[dry-run] git init + commit + push $dir -> $ORG/$name"
    return 0
  fi
  (
    cd "$dir"
    git init -q
    git add -A
    git -c user.name="gamAI Labs" -c user.email="labs@gamai.io" \
        commit -qm "v0.1.0: initial public release"
    git branch -M main
    git remote add origin "https://x-access-token:$GH_TOKEN@github.com/$ORG/$name.git"
    git push -q -u origin main
    git remote set-url origin "https://github.com/$ORG/$name.git"
  )
  echo "pushed $ORG/$name"
}

create_repo proofgate "Fail-closed evidence gate for agent claims"
create_repo agent-immunity "Learned antibodies and provenance taint for AI agents"
create_repo crossnode-bench "Benchmark that measures agent claims against ground truth"

push_component proofgate proofgate
push_component agent-immunity agent-immunity
push_component crossnode-bench crossnode-bench

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "Dry run complete. Re-run with --yes to create and push."
  echo "Then publish the root meta-repo manually (or repeat this pattern for it)."
fi
