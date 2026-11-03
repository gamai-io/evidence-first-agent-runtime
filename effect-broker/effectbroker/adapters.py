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
