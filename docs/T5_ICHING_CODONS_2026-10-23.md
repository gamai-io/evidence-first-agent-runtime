# T5 — I Ching 64 vs 64 codons (negative control)

Question: does the equality 64 hexagrams = 64 codons carry structural evidence?

Method: Fu Xi binary order 0..63 as 6-bit vectors; codons mapped to 6 bits
(A=00, C=01, G=10, T=11); 64x64 Hamming matrices; Mantel test with 10,000
permutations.

Result: `r = 1.0, p = 0.0001`.

Interpretation: **not evidence.** The 6-bit mapping is distance-preserving and
both sides are the same full hypercube, so `r = 1` is constructed by the
mapping. The p-value is meaningless here. This is exactly the "64 = 2^6 vs
4^3" arithmetic coincidence, not a biological signal.

Verdict: the naive count comparison is **non-identifiable**. Any claim of a
hexagram–codon code needs an independent, pre-registered mapping and an
out-of-sample test; this test cannot supply one.

Artifacts: `labs/iching_codons.py`, `labs/iching_codons_results.json`.
