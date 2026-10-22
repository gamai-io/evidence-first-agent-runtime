# T4 — 40 Hz gamma literature gate

This is a **scoping audit**, not a meta-analysis. OpenAlex metadata/abstracts
only; no full-text effect sizes, no GRADE, no pooled estimate.

## Queries

- `"40 Hz" gamma entrainment Alzheimer`
- `"40 Hz" gamma sensory stimulation randomized`
- `gamma entrainment cognition randomized`

2015+, deduplicated by DOI/OpenAlex id.

## Result

| Metric | Count |
|---|---:|
| unique works | 133 |
| human works | 70 |
| human randomized/sham-like | 18 |
| animal works | 34 |
| relevant after screening* | **6** |

\* excludes reviews/protocols/tACS/tDCS/tRNS/vibroacoustic/fibromyalgia and
requires Alzheimer/cognitive context.

**Verdict:** fewer than 10 relevant human RCT-like records → **meta-analysis is
not justified yet**. The 6 candidates need full-text screening; abstracts are
not enough to extract effects.

## What this means

- The literature contains real 40 Hz work, but it is heterogeneous: mouse
  studies, pilot/feasibility studies, protocols, reviews, and other
  neuromodulation methods.
- Do not claim a pooled gamma effect, and do not use 40 Hz as evidence for
  cymatics/DNA claims.
- A real meta-analysis needs pre-registered inclusion, full-text extraction,
  risk-of-bias and a prediction interval; that is a separate study.

## Reproduce

```bash
python3 labs/gamma_audit.py
```

Artifact: `labs/gamma_audit_results.json`. Network required.
