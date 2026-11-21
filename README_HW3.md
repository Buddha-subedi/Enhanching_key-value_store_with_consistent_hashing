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

For Windows PowerShell, use the same commands. If an older standalone container occupies a port, remove it with `docker rm -f key-value-store` before Compose startup. Wait for the router health check before integration tests: `Invoke-RestMethod http://localhost:8000/health`. The November 21 follow-up PowerShell output reported **4 passed in 113.76 seconds** for `test_hash_ring.py` and `test_integration_hw3.py`. See `results/validation_observations.md` for the user-reported verification; capture a fresh complete transcript using `HW3_HISTORY_COMMANDS.md`.

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

## Measured results (latest CSV in November 21, 2026 upload)

Command: `python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3`.

| Active nodes | Mean throughput (ops/s) | Mean latency (ms) | Mean P95 latency (ms) | Errors | Throughput vs. 1 node |
|---|---:|---:|---:|---:|---:|
| 1 | 99.33 | 159.79 | 359.94 | 0 | 1.000x |
| 2 | 97.45 | 163.14 | 383.88 | 0 | 0.981x |
| 3 | 94.02 | 169.76 | 368.69 | 0 | 0.947x |

All 10,800 timed operations succeeded (3 repeats × 1,200 operations × 3 configurations). Two nodes changed throughput by -1.89% relative to one; three nodes changed throughput by -5.35%. These are small-sample single-host results. See [REPORT_HW3.md](REPORT_HW3.md) for the full nine-run table, interpretation, limitations, and environment.

### Performance plots

These paths refer to files generated on the local computer by `python plot_hw3.py`. Add the actual PNG files and `results/benchmark.csv` to the GitHub repository for the links and images to work.

![Throughput](results/throughput.png)
![Mean latency](results/latency_mean.png)
![P95 latency](results/latency_p95.png)

## Verified and pending tests

- Verified in earlier standalone transcript: CRUD, validation, missing-key handling, concurrency, and Docker-volume persistence.
- Verified in distributed transcript: Compose image/container startup, nine timed 1/2/3-node benchmark runs, zero reported errors, and plot-file generation.
- User-reported follow-up: `4 passed in 113.76s`, membership `kv1/kv2/kv3`, 3,000/3,000 PUTs successful, and distribution 986/962/1052. This evidence is transcribed from the interactive session, not independently executed on the Windows host.
- Not demonstrated: automatic node-failure recovery/failover; not required explicitly by the assignment.
- Consistent hashing partitions data; it does **not** replicate data or guarantee availability after a backend failure.

## Submission checklist
- [x] Run `python -m pytest -q test_hash_ring.py test_integration_hw3.py` (4 passed, user-reported; capture again in new transcript)
- [x] Run distributed 1/2/3-node benchmark on local computer
- [x] Include `results/benchmark.csv` and all three PNG plots (present in this ZIP)
- [x] Fill measured values in `REPORT_HW3.md` and discuss observed trends
- [x] Document Docker CPU/RAM allocation, OS, Docker version and limitations
- [x] Zip source, results, and completed report for submission

## Important design note
The ring **partitions** data. It does not replicate data or provide automatic failover. Rebalancing pauses gateway traffic and requires all relevant backend containers to be reachable. This is a correct small-scale coursework architecture, not a production fault-tolerant distributed database.

## Direct key distribution check (November 21 follow-up)

With all three nodes active, 3,000 PUTs completed with zero reported failures. The router distribution endpoint returned **kv1: 986 (32.87%), kv2: 962 (32.07%), kv3: 1,052 (35.07%)**, total **3,000**. Ideal equal share is 1,000 keys each. This verifies reasonably balanced physical storage for the tested keys; it is not a throughput result. See `results/validation_observations.md`. For a complete reproducible command-by-command Windows PowerShell transcript, follow `HW3_HISTORY_COMMANDS.md`.


## Latest benchmark data provenance (November 21 ZIP)

The figures and tables above are calculated directly from the uploaded `results/benchmark.csv` (nine runs). The included PNG plots should be regenerated with `python plot_hw3.py` if CSV data changes. The 3,000-key distribution and four passing tests are separately recorded observations, not measurements from the benchmark CSV.
