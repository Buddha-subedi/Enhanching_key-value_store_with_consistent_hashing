# Homework 3 — Distributed KV Store (Flask + SQLite + Consistent Hashing)

This project extends a Dockerized Flask/SQLite KV store with a consistent-hashing router and three independently persisted backend partitions. It includes a measured 1/2/3-active-node benchmark performed on November 20, 2026. Original Assignment 2 scripts remain included.

## Quick start
Requires Docker Engine with Compose v2, and Python 3.11+ for tests/plots.

```bash
docker compose up -d --build
python -m pip install -r requirements-dev.txt
python -m pytest -q test_hash_ring.py test_integration_hw3.py
python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3
python plot_hw3.py
```

For Windows PowerShell, use the same commands. If an older standalone container occupies a port, remove it with `docker rm -f key-value-store` before Compose startup. Wait for the router health check before integration tests: `Invoke-RestMethod http://localhost:8000/health`. The uploaded execution transcript confirms the Compose build and benchmark, **but does not record running the hash-ring and integration pytest commands**.

## HTTP API
```bash
curl -X PUT http://localhost:8000/hello -H "Content-Type: application/json" -d '{"value":"world"}'
curl http://localhost:8000/hello
curl -X DELETE http://localhost:8000/hello
```

## Membership and distribution
```bash
curl -X POST http://localhost:8000/_admin/membership -H "X-Admin-Token: local-dev-token" -H "Content-Type: application/json" -d '{"nodes":["kv1","kv2"]}'
curl -H "X-Admin-Token: local-dev-token" http://localhost:8000/_admin/distribution
```

Then change nodes to `["kv1","kv2","kv3"]` to scale to three, or `["kv1"]` to scale back to one. The benchmark automatically performs the 1→2→3 transitions. All three containers are running throughout; **active store count**, not container startup count, changes. This keeps startup time outside the performance measurements.

**Security:** change `ROUTER_ADMIN_TOKEN` in a real deployment. The default token is only for local coursework. All backends share a private Docker network. Do not expose backend ports publicly.

## Measured results (November 20, 2026)

Command: `python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3`.

| Active nodes | Mean throughput (ops/s) | Mean latency (ms) | Mean P95 latency (ms) | Errors | Throughput vs. 1 node |
|---|---:|---:|---:|---:|---:|
| 1 | 95.61 | 167.17 | 386.94 | 0 | 1.000x |
| 2 | 97.54 | 162.77 | 384.97 | 0 | 1.020x |
| 3 | 82.94 | 197.45 | 447.69 | 0 | 0.867x |

All 10,800 timed operations succeeded (3 repeats × 1,200 operations × 3 configurations). Two nodes performed marginally better than one; three nodes performed worse on average in this single-host test. See [REPORT_HW3.md](REPORT_HW3.md) for the full nine-run table, interpretation, limitations, and environment.

### Performance plots

These paths refer to files generated on the local computer by `python plot_hw3.py`. Add the actual PNG files and `results/benchmark.csv` to the GitHub repository for the links and images to work.

![Throughput](results/throughput.png)
![Mean latency](results/latency_mean.png)
![P95 latency](results/latency_p95.png)

## Verified and pending tests

- Verified in earlier standalone transcript: CRUD, validation, missing-key handling, concurrency, and Docker-volume persistence.
- Verified in distributed transcript: Compose image/container startup, nine timed 1/2/3-node benchmark runs, zero reported errors, and plot-file generation.
- Not shown as executed: `test_hash_ring.py`, `test_integration_hw3.py`, direct storage-distribution inspection, or node-failure/failover tests.
- Consistent hashing partitions data; it does **not** replicate data or guarantee availability after a backend failure.

## Submission checklist
- [ ] Run `python -m pytest -q test_hash_ring.py test_integration_hw3.py` and capture passing output (not in supplied transcript)
- [x] Run distributed 1/2/3-node benchmark on local computer
- [ ] Commit actual `results/benchmark.csv` and three generated PNG plots (created locally; not provided here)
- [x] Fill measured values in `REPORT_HW3.md` and discuss observed trends
- [x] Document Docker CPU/RAM allocation, OS, Docker version and limitations
- [ ] Zip source, results, and completed report for submission

## Important design note
The ring **partitions** data. It does not replicate data or provide automatic failover. Rebalancing pauses gateway traffic and requires all relevant backend containers to be reachable. This is a correct small-scale coursework architecture, not a production fault-tolerant distributed database.
