#!/usr/bin/env bash
# Create (or reuse) a disposable Vultr instance for the rush sandbox.
# Usage: ./deploy_vultr.sh [up|down|status]
set -euo pipefail

API="https://api.vultr.com/v2"
KEY="${VULTR_API_KEY:?set VULTR_API_KEY}"
PLAN="${VULTR_PLAN:-vc2-1c-1gb}"
REGION="${VULTR_REGION:-fra}"
OS_ID="${VULTR_OS_ID:-2284}"       # Ubuntu 24.04 x64
LABEL="${VULTR_LABEL:-rush-sandbox}"
SSHKEY_NAME="${VULTR_SSHKEY_NAME:-rush-hackathon}"
TAG="rush"

api() { curl -s -4 -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' "$@"; }

find_instance() {
  api "$API/instances?per_page=100" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('instances',[])
for i in d:
    if i.get('label')=='$LABEL' and i.get('status') in ('active','pending','installing'):
        print(i['id']); break
"
}

case "${1:-status}" in
  up)
    ID=$(find_instance || true)
    if [ -n "${ID:-}" ]; then echo "exists: $ID"; else
      KEYID=$(api "$API/ssh-keys" | python3 -c "
import sys,json
for k in json.load(sys.stdin).get('ssh_keys',[]):
    if k['name']=='$SSHKEY_NAME': print(k['id']); break
")
      BODY=$(python3 - "$PLAN" "$REGION" "$OS_ID" "$LABEL" "$KEYID" "$TAG" <<'PY'
import json,sys
plan,region,osid,label,keyid,tag=sys.argv[1:7]
ud = """#!/bin/bash
set -eux
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io python3 python3-venv git curl
systemctl enable --now docker
ufw allow 8098/tcp || true
mkdir -p /work && chmod 777 /work
"""
print(json.dumps({"region":region,"plan":plan,"os_id":int(osid),"label":label,
                  "sshkey_id":[keyid],"tags":[tag],"user_data":ud,
                  "hostname":label,"backups":"disabled"}))
PY
)
      ID=$(api -X POST "$API/instances" -d "$BODY" | python3 -c "import sys,json;print(json.load(sys.stdin)['instance']['id'])")
      echo "created: $ID"
    fi
    for _ in $(seq 1 60); do
      read -r ST IP < <(api "$API/instances/$ID" | python3 -c "
import sys,json
i=json.load(sys.stdin)['instance']; print(i.get('status'), i.get('main_ip','0.0.0.0'))")
      echo "status=$ST ip=$IP"
      [ "$ST" = "active" ] && [ "$IP" != "0.0.0.0" ] && { echo "$IP" > .vultr_host; break; }
      sleep 10
    done
    ;;
  down)
    ID=$(find_instance || true)
    [ -n "${ID:-}" ] && api -X DELETE "$API/instances/$ID" && echo "deleted: $ID" || echo "nothing to delete"
    rm -f .vultr_host
    ;;
  status)
    api "$API/instances?per_page=100" | python3 -c "
import sys,json
for i in json.load(sys.stdin).get('instances',[]):
    if 'rush' in (i.get('tags') or []) or i.get('label','').startswith('rush'):
        print(i['id'], i['status'], i.get('main_ip'), i.get('plan'), i.get('label'))
"
    ;;
esac
