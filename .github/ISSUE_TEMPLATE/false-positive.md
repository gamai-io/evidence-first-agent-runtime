---
name: False positive (immunity)
about: Benign text blocked by the shield or near-miss matcher
labels: immunity, false-positive
---

**Text (redact anything private):**

```

```

**Tool / channel:** (answer, doc, shell, memory, ...)

**Observed:** `allow: false`, reason: ...

**Why it is benign:**

**Reproduction:**

```bash
python3 - <<'PY'
from immunity import Store
# minimal snippet
PY
```
