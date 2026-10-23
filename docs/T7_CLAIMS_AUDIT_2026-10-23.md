# T7 — occult/wellness claims: a naive bibliometric screen fails

Method: one broad OpenAlex free-text query per claim, top-3 by citations.
This is **not** a systematic review and **not** evidence for or against a claim.

| Claim | OpenAlex hits | Editorial status |
|---|---:|---|
| 528 Hz repairs DNA | 3,002 | no controlled evidence |
| Solfeggio frequencies heal | 327 | no controlled evidence |
| DNA has a specific electromagnetic frequency | 49,156 | mechanism real; "frequency code" unproven |
| Water memory (Benveniste) | 4,362 | not replicated |
| Chakras are measurable organs | 1,334 | no anatomical evidence |
| Meditation changes brain structure | 37,791 | supported by trials |
| 40 Hz gamma helps Alzheimer's | 5,701 | early/limited trials |
| I Ching 64 maps to 64 codons | 21,551 | arithmetic coincidence |
| Pyramids focus energy | 140,663 | no credible evidence |
| Piezo1 mediates mechanotransduction | 6,542 | strong evidence |

## The methodological finding

The counts are useless as evidence. Examples of top "hits":
- "528 Hz DNA repair" -> *Nature's hierarchical materials* (2007)
- "Pyramids focus energy" -> *Image-to-Image Translation with Conditional
  Adversarial Networks* (2017)
- "I Ching 64 = codons" -> *Hallmarks of aging* (2023)
- "Chakras measurable" -> a silver-nanoparticle review

Broad free-text search retrieves words, not claims. A real audit needs
pre-registered claim operationalization, precise queries, inclusion/exclusion,
and primary-source appraisal.

## Status

The editorial verdicts above are a starting map, not a peer-reviewed
conclusion. Claims 1, 2, 4, 5 and 9 have no controlled evidence in this
screen; 6 is supported; 7 is early; 10 is strong; 3 conflates a real
mechanism with an unproven "frequency code"; 8 is arithmetic (see T5).

Artifacts: `labs/claims_audit.py`, `labs/claims_audit_results.json`.
