#!/usr/bin/env bash
set -eux
export DEBIAN_FRONTEND=noninteractive
if [ ! -d /opt/rush-src/.git ]; then
  git clone --depth 1 https://github.com/gamai-io/evidence-first-agent-runtime /opt/rush-src
else
  cd /opt/rush-src && git fetch --depth 1 origin main && git reset --hard origin/main
fi
python3 -m venv /opt/rush-venv
/opt/rush-venv/bin/pip install -q --upgrade pip
/opt/rush-venv/bin/pip install -q fastapi uvicorn
cat >/etc/systemd/system/gama-rush.service <<'UNIT'
[Unit]
Description=gamAI rush - Blast Radius Zero
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/rush-src
Environment=RUSH_EXECUTOR=docker
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/rush-venv/bin/uvicorn rush.app:app --host 0.0.0.0 --port 8098
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now gama-rush
sleep 4
curl -fsS http://127.0.0.1:8098/health
