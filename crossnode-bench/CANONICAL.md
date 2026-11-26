# Canonical repository

This `crossnode-bench/` directory is a **pinned vendored mirror**.

The canonical, authoritative source is:
**https://github.com/gamai-io/crossnode-bench**

Please open issues / PRs / releases there. This copy is pinned to commit
`962977072059ea5ba13dad2114c71d40dcb62f95` (`v1.5.0-17-g9629770`) and is kept
only because the upstream repository has no `pyproject.toml`/`setup.py`, so pip
cannot install it. `tools/check_vendored.py` compares the Python files against
that commit every week. Once upstream ships packaging metadata, delete this
directory and add the package to `requirements-vendored.txt`.
