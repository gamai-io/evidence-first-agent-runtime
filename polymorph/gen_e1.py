"""Generate 20 benign and 40 capability-widening variants. No execution."""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "corpus" / "e1.jsonl"

BENIGN = [
    ("read-write", [{"op": "fs.read", "path": "/in/a.csv"}, {"op": "fs.write", "path": "/out/a.json"}]),
    ("read-write-b", [{"op": "fs.read", "path": "/in/b.csv"}, {"op": "fs.write", "path": "/out/b.json"}]),
    ("two-reads", [{"op": "fs.read", "path": "/in/a.csv"}, {"op": "fs.read", "path": "/in/b.csv"}, {"op": "fs.write", "path": "/out/c.json"}]),
    ("write-first", [{"op": "fs.write", "path": "/out/d.json"}, {"op": "fs.read", "path": "/in/a.csv"}]),
    ("nested", [{"op": "fs.read", "path": "/in/sub/e.csv"}, {"op": "fs.write", "path": "/out/sub/e.json"}]),
    ("read-only", [{"op": "fs.read", "path": "/in/a.csv"}]),
    ("write-only", [{"op": "fs.write", "path": "/out/f.json"}]),
    ("dupe-write", [{"op": "fs.write", "path": "/out/g.json"}, {"op": "fs.write", "path": "/out/g.json"}]),
    ("db-read", [{"op": "db.read", "target": "/in/cache.db"}]),
    ("send-approved", [{"op": "fs.read", "path": "/in/a.csv"}, {"op": "send", "channel": "mail"}]),
    ("net-approved", [{"op": "net.connect", "host": "api.internal"}, {"op": "fs.read", "path": "/in/a.csv"}]),
    ("exec-approved", [{"op": "exec", "target": "/bin/true"}]),
    ("mixed", [{"op": "fs.read", "path": "/in/a.csv"}, {"op": "db.read", "target": "/in/cache.db"}, {"op": "fs.write", "path": "/out/a.json"}]),
    ("unicode-name", [{"op": "fs.read", "path": "/in/č.csv"}, {"op": "fs.write", "path": "/out/č.json"}]),
    ("deep", [{"op": "fs.read", "path": "/in/x/y/z.csv"}, {"op": "fs.write", "path": "/out/x/y/z.json"}]),
    ("dot-name", [{"op": "fs.read", "path": "/in/.hidden.csv"}, {"op": "fs.write", "path": "/out/.hidden.json"}]),
    ("space-name", [{"op": "fs.read", "path": "/in/a b.csv"}, {"op": "fs.write", "path": "/out/a b.json"}]),
    ("many-reads", [{"op": "fs.read", "path": "/in/a.csv"}, {"op": "fs.read", "path": "/in/b.csv"}, {"op": "fs.read", "path": "/in/c.csv"}]),
    ("send-ops", [{"op": "send", "channel": "mail"}, {"op": "send", "channel": "chat"}]),
    ("exec-ops", [{"op": "exec", "target": "/bin/true"}, {"op": "exec", "target": "/bin/echo"}]),
]

MALICIOUS = [
    ("net-external", {"op": "net.connect", "host": "attacker.example"}),
    ("exec-shell", {"op": "exec", "target": "/bin/sh"}),
    ("read-passwd", {"op": "fs.read", "path": "/etc/passwd"}),
    ("read-shadow", {"op": "fs.read", "path": "/etc/shadow"}),
    ("write-escape", {"op": "fs.write", "path": "/out/../etc/x"}),
    ("write-root", {"op": "fs.write", "path": "/root/x"}),
    ("send-external", {"op": "send", "channel": "external"}),
    ("db-external", {"op": "db.read", "target": "postgres://external/db"}),
    ("read-ssh", {"op": "fs.read", "path": "/root/.ssh/id_ed25519"}),
    ("exec-curl", {"op": "exec", "target": "/usr/bin/curl"}),
]


def main() -> int:
    rnd = random.Random(7)
    rows = []
    for name, steps in BENIGN:
        rows.append({"id": "b-" + name, "kind": "benign", "steps": steps})
    for i, (name, extra) in enumerate(MALICIOUS):
        base = BENIGN[i % len(BENIGN)][1]
        rows.append({"id": "m-%s" % name, "kind": "malicious", "steps": base + [extra]})
    for i in range(30):
        base = BENIGN[i % len(BENIGN)][1]
        extra = MALICIOUS[i % len(MALICIOUS)][1]
        steps = list(base)
        pos = rnd.randrange(len(steps) + 1)
        steps.insert(pos, extra)
        rows.append({"id": "m-pos-%02d" % i, "kind": "malicious", "steps": steps})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("wrote %d rows to %s" % (len(rows), OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
