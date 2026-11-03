import dataclasses
import os
import tempfile
import unittest

from effectbroker import (
    Broker,
    Evidence,
    FileAdapter,
    GrantInvalid,
    Intent,
    Policy,
    SqliteAdapter,
    digest_bytes,
    run_all,
)


def sha(s):
    return digest_bytes(s.encode())


class TestAttackSuite(unittest.TestCase):
    def test_all_eight_attacks_detected(self):
        result = run_all()
        self.assertEqual(result["total"], 8)
        self.assertEqual(result["passed"], 8, result["results"])
        self.assertTrue(result["chain_valid"])
        self.assertEqual(len(result["merkle_root"]), 64)


class TestHappyPath(unittest.TestCase):
    def _file_broker(self, tmp):
        root = os.path.join(tmp, "root")
        os.makedirs(root, exist_ok=True)
        ev = Evidence(os.path.join(tmp, "evidence.jsonl"))
        broker = Broker({"file.write": FileAdapter(root)}, policy=Policy(actions={"file.write": {}}), evidence=ev)
        return broker, root, ev

    def test_commit_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            broker, root, ev = self._file_broker(tmp)
            intent = Intent("t1", "file.write", "out/a.txt", "out", sha("hello"))
            grant = broker.authorize(intent)
            effect = broker.execute(grant, {"content": "hello"})
            result = broker.commit(effect, "success")
            self.assertEqual(result["verdict"], "pass")
            token = result["token"]
            self.assertTrue(broker.verify(token)["ok"])
            self.assertTrue(ev.chain_valid())
            with open(os.path.join(root, "out/a.txt"), "rb") as f:
                self.assertEqual(f.read(), b"hello")

    def test_idempotency_single_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            broker, root, _ = self._file_broker(tmp)
            intent = Intent("t1", "file.write", "out/a.txt", "out", sha("hello"), idempotency_key="k1")
            e1 = broker.execute(broker.authorize(intent), {"content": "hello"})
            e2 = broker.execute(broker.authorize(intent), {"content": "hello"})
            self.assertEqual(e1.effect_id, e2.effect_id)

    def test_tampered_token_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            broker, _, _ = self._file_broker(tmp)
            intent = Intent("t1", "file.write", "out/a.txt", "out", sha("hello"))
            effect = broker.execute(broker.authorize(intent), {"content": "hello"})
            token = broker.commit(effect, "success")["token"]
            bad = dataclasses.replace(token, probe={"ok": True, "sha256": "0" * 64})
            with self.assertRaises(GrantInvalid):
                broker.verify(bad)


class TestSqlAdapter(unittest.TestCase):
    def test_system_of_record_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "broker.db")
            adapter = SqliteAdapter(db)
            broker = Broker({"sql.insert": adapter}, policy=Policy(actions={"sql.insert": {}}), evidence=Evidence())
            intent = Intent("t1", "sql.insert", "items:k1", "items", sha("value-1"))
            effect = broker.execute(broker.authorize(intent), {"value": "value-1"})
            result = broker.commit(effect, "success")
            self.assertEqual(result["verdict"], "pass")
            self.assertTrue(broker.verify(result["token"])["ok"])


if __name__ == "__main__":
    unittest.main()
