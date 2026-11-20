# Homework 3 — Distributed KV Store (Flask + SQLite + Consistent Hashing)

This project **extends the uploaded Dockerized KV store**; original Assignment 2 scripts remain included.

## Quick start
Requires Docker Engine with Compose v2, and Python 3.11+ for tests/plots.

```bash
docker compose up -d --build
python -m pip install -r requirements-dev.txt
python -m pytest -q test_hash_ring.py test_integration_hw3.py
python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3
python plot_hw3.py
```

For Windows PowerShell use the same commands. Wait for the router health check before integration tests: `curl http://localhost:8000/health`.

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

## Submission checklist
- [ ] Run tests and capture passing output
- [ ] Run benchmark on your own computer
- [ ] Include actual `results/benchmark.csv` and three generated PNG plots
- [ ] Replace TBD values in `REPORT_HW3.md` and discuss observed trends
- [ ] Document machine CPU/RAM/OS, Docker version and limitations
- [ ] Zip source, results, and completed report for submission

## Important design note
The ring **partitions** data. It does not replicate data or provide automatic failover. Rebalancing pauses gateway traffic and requires all relevant backend containers to be reachable. This is a correct small-scale coursework architecture, not a production fault-tolerant distributed database.
