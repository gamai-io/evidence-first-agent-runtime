# Contributing

Thanks for trying to break this. That is the point.

## Before a PR

1. `./repro.sh` must be green.
2. Add a test that fails before your change and passes after it.
3. For a new detection or predicate, include a false-positive case and explain
   why it is acceptable.
4. No new dependencies. Standard library only, Python 3.10+.
5. No secrets, no private hosts, no customer data. Run
   `launch/sanitize.sh` before pushing.

## Good first issues

- Add a predicate to `proofgate` (e.g. `date_within`, `set_equals`) with tests.
- Add a channel or payload class to `agent-immunity/eval.py`.
- Add an adapter to `crossnode-bench` (SSH, ADB, a specific daemon) with a
  recorded fixture.

## Review bar

A change is accepted when it (a) has a reproducible failing case, (b) does not
weaken fail-closed behavior, and (c) keeps the false-positive rate visible.
