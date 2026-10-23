# T6 — k-mer/CGR fractal dimension (negative result)

Question: is there a useful "fractal genome signature" in k-mer space?

Method: NCBI RefSeq sequences (SARS-CoV-2, E. coli K-12, human mtDNA, yeast
chr1; first 200 kb), CGR with A/C/G/T corners, 256×256 occupancy, box-counting
at eight scales, 5 mononucleotide-shuffled controls per genome.

| Genome | bp used | D real | D shuffled | Δ | z |
|---|---:|---:|---:|---:|---:|
| SARS-CoV-2 | 29,903 | 1.8173 | 1.8412 | -0.0238 | -38.0 |
| E. coli K-12 | 200,000 | 1.9746 | 1.9936 | -0.0189 | -251.0 |
| human mtDNA | 16,569 | 1.7324 | 1.7454 | -0.0129 | -12.5 |
| yeast chr1 | 200,000 | 1.9780 | 1.9837 | -0.0057 | -27.8 |

Interpretation: all dimensions are close to 2. Real genomes are slightly
lower than their mononucleotide-shuffled controls, but the effect is tiny
(Δ ≤ 0.024) and the huge z-values come from the near-zero variance of the
shuffle, not from a strong signal. This is k-mer/composition bias, not
evidence of a special fractal "genome code", and it is not a useful
classifier. Dinucleotide-preserving surrogates were not tested; that is the
next control if this is pursued.

Artifacts: `labs/kmer_fractal.py`, `labs/kmer_fractal_results.json`.
