import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT/"proofgate"):
    sys.path.insert(0, str(p))
from proofgate import attest_claims, check_attested

class ClaimSourceGap(unittest.TestCase):
    def test_rejects_untrusted_claim_source_even_if_arg_trusted(self):
        claims = attest_claims([{"predicate":"eq_num","expected":4,"observed":4}], key=b"k", source="model")
        r = check_attested(claims, key=b"k", source="executor")
        self.assertFalse(r["ok"], "claim signed by 'model' accepted with arg 'executor'")
    def test_accepts_matching_trusted_source(self):
        claims = attest_claims([{"predicate":"eq_num","expected":4,"observed":4}], key=b"k", source="executor")
        self.assertTrue(check_attested(claims, key=b"k", source="executor")["ok"])

if __name__ == "__main__":
    unittest.main()
