# Fleet runners for crossnode-bench

These scripts ran the benchmark against the real GAMA fleet (one task per node,
`gama --json hc <node> shell ...`). They are **this umbrella's** code; the
benchmark itself is installed from its own repository.

`crossnode-bench` up to v1.5 did not accept fleet nodes, so the vendored copy
carried two adapters (`FleetNode`, `CliNode`) and two extra config types. Those
adaptations now live in [`fleet_nodes.py`](fleet_nodes.py) and subclass the
installed `crossnode.Node`; the benchmark is used unchanged.

```bash
python3 -m pip install -r requirements-vendored.txt   # gets crossnode-bench
python3 bench/crossnode_fleet/real1000.py --nodes oracle,linux3,vast,kuca,podrum
python3 bench/crossnode_fleet/scale1000.py            # local, no fleet needed
```

`real1000*.py` need a reachable `gama` CLI and a fleet lease; they are not part
of `repro.sh` and are not run in CI. `scale1000.py` only needs a local shell.
Reports are written under `runs/` next to the script.
