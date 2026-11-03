import sys

from .attacks import run_all


def main(argv=None):
    result = run_all()
    width = max(len(r["attack"]) for r in result["results"])
    print("EFFECT BROKER — attack suite")
    print("=" * (width + 30))
    for r in result["results"]:
        status = "PASS" if r["pass"] else "FAIL"
        print("%-*s  %-6s  %s" % (width, r["attack"], status, r["observed"]))
    print("-" * (width + 30))
    print("passed=%d/%d  chain_valid=%s  merkle_root=%s" % (
        result["passed"], result["total"], result["chain_valid"], result["merkle_root"]))
    print("evidence_records=%d" % result["records"])
    return 0 if result["passed"] == result["total"] and result["chain_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
