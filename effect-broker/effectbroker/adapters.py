import os
import sqlite3

from .core import digest_bytes


def _sha_text(v: str) -> str:
    return digest_bytes(v.encode())


class FileAdapter:
    action = "file.write"

    def __init__(self, root):
        self.root = os.path.realpath(root)

    def scope_ok(self, target, scope):
        scope_abs = os.path.realpath(os.path.join(self.root, scope))
        target_abs = os.path.realpath(os.path.join(self.root, target))
        if scope_abs != self.root and not scope_abs.startswith(self.root + os.sep):
            return False
        return target_abs == scope_abs or target_abs.startswith(scope_abs + os.sep)

    def _path(self, target):
        return os.path.join(self.root, target)

    def execute(self, intent, payload):
        content = payload.get("content")
        if isinstance(content, str):
            data = content.encode()
        elif isinstance(content, bytes):
            data = content
        else:
            raise ValueError("payload.content must be str or bytes")
        path = self._path(intent.target)
        os.makedirs(os.path.dirname(path) or self.root, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return {"path": intent.target, "sha256": digest_bytes(data), "size": len(data)}

    def probe(self, intent, effect=None):
        path = self._path(intent.target)
        if not os.path.isfile(path):
            return {"ok": False, "reason": "M1_no_effect", "sha256": None, "mismatch": "M1"}
        with open(path, "rb") as f:
            data = f.read()
        sha = digest_bytes(data)
        expected = intent.expected if isinstance(intent.expected, str) else (intent.expected or {}).get("sha256")
        ok = expected is not None and sha == expected
        return {"ok": ok, "sha256": sha, "expected": expected, "size": len(data), "mismatch": None if ok else "M2"}


class SqliteAdapter:
    action = "sql.insert"

    def __init__(self, db_path, tables=("items",)):
        self.db_path = db_path
        self.tables = set(tables)
        with sqlite3.connect(self.db_path) as c:
            for t in self.tables:
                c.execute("CREATE TABLE IF NOT EXISTS %s (key TEXT PRIMARY KEY, value TEXT NOT NULL)" % t)
            c.commit()

    @staticmethod
    def _split(target):
        if ":" not in target:
            raise ValueError("target must be <table>:<key>")
        table, key = target.split(":", 1)
        if not table or not key or len(key) > 128 or "/" in key or "\x00" in key:
            raise ValueError("invalid key")
        return table, key

    def scope_ok(self, target, scope):
        try:
            table, _ = self._split(target)
        except ValueError:
            return False
        return table in self.tables and table == scope

    def execute(self, intent, payload):
        table, key = self._split(intent.target)
        value = payload.get("value")
        if not isinstance(value, str):
            raise ValueError("payload.value must be str")
        with sqlite3.connect(self.db_path) as c:
            c.execute("INSERT OR REPLACE INTO %s (key, value) VALUES (?, ?)" % table, (key, value))
            c.commit()
        return {"table": table, "key": key, "value_sha256": _sha_text(value)}

    def probe(self, intent, effect=None):
        table, key = self._split(intent.target)
        with sqlite3.connect(self.db_path) as c:
            row = c.execute("SELECT value FROM %s WHERE key = ?" % table, (key,)).fetchone()
        if row is None:
            return {"ok": False, "reason": "M1_no_effect", "sha256": None, "mismatch": "M1"}
        sha = _sha_text(row[0])
        expected = intent.expected if isinstance(intent.expected, str) else (intent.expected or {}).get("sha256")
        ok = expected is not None and sha == expected
        return {"ok": ok, "sha256": sha, "expected": expected, "mismatch": None if ok else "M2"}


class HttpAdapter:
    action = "http.get"

    def __init__(self, allowed_hosts=("127.0.0.1", "localhost"), allowed_ports=None, timeout=5.0):
        self.allowed_hosts = set(allowed_hosts)
        self.allowed_ports = set(allowed_ports) if allowed_ports else None
        self.timeout = timeout

    @staticmethod
    def _parts(url):
        from urllib.parse import urlparse

        p = urlparse(url)
        port = p.port or (443 if p.scheme == "https" else 80)
        return p, p.scheme, p.hostname, port

    def scope_ok(self, target, scope):
        try:
            _, scheme, host, port = self._parts(target)
        except Exception:
            return False
        if scheme not in ("http", "https") or host not in self.allowed_hosts:
            return False
        if self.allowed_ports is not None and port not in self.allowed_ports:
            return False
        return scope == "%s:%s" % (host, port)

    def _get(self, url):
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "effect-broker-probe/0.1"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return r.status, r.read(1_000_000)

    def execute(self, intent, payload=None):
        status, data = self._get(intent.target)
        return {"url": intent.target, "status": status, "sha256": digest_bytes(data), "size": len(data)}

    def probe(self, intent, effect=None):
        try:
            status, data = self._get(intent.target)
        except Exception as exc:
            return {"ok": False, "reason": "M1_probe_failed", "mismatch": "M1", "error": str(exc)[:120], "sha256": None}
        sha = digest_bytes(data)
        expected = intent.expected if isinstance(intent.expected, str) else (intent.expected or {}).get("sha256")
        ok = 200 <= status < 300 and expected is not None and sha == expected
        return {"ok": ok, "sha256": sha, "expected": expected, "status": status, "size": len(data), "mismatch": None if ok else "M2"}
