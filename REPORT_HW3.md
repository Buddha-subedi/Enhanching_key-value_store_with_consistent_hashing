# Assignment 3 — Distributed KV Store with Consistent Hashing

## 1. Objective
Extend the prior Flask/SQLite HTTP KV store to distribute keys across one, two, and three independent instances using consistent hashing, and compare end-to-end throughput and latency under identical workloads.

## 2. Baseline and architecture
The supplied Assignment 2 server (`server.py`) retains its SQLite database and CRUD API. A new Flask router (`router.py`) forwards requests to one of three backend instances (`kv1`, `kv2`, `kv3`). Each backend has its **own named Docker volume**, so the instances are separate partitions, not replicas. All external traffic enters through port 8000. Docker internal networking hides backend ports from the host.

## 3. Hashing algorithm
`hash_ring.py` hashes each node identifier and 128 virtual-node indices using SHA-256 and sorts these positions. A key is assigned to the first virtual node clockwise from SHA-256(key), wrapping at the end. Virtual nodes improve distribution across a small number of physical servers. When a node joins, only keys now assigned to that node should change ownership. This is tested using 10,000 synthetic keys.

## 4. Scaling and data integrity
The authenticated membership endpoint accepts `{"nodes":["kv1","kv2"]}`. It locks all router requests, inventories existing backend keys, copies keys to their new owners, verifies successful HTTP writes, switches the active ring, and cleans up stale copies. Existing data remains accessible across 1→2→3→2→1 membership transitions. Migration is intentionally synchronous and pauses traffic; for production, a distributed coordination service, transactional migration, streaming, authentication between services, and redundancy would be necessary. An unreachable backend returns an error; consistent hashing **does not provide fault tolerance or replication by itself**.

## 5. Experimental method
Use `docker compose up -d --build`, then `pytest -q test_hash_ring.py test_integration_hw3.py`. Run `python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3 --read-fraction 0.8` and `python plot_hw3.py`. The benchmark seeds keys before each timed run, uses an 80% read/20% update workload with 128-byte values, measures only timed operations, and cleans up after. Identical concurrency and operation counts are used at each node count. It reports successful operations/elapsed seconds, mean, P50, P95 and P99 per-request latency, and errors. Repeat runs and note system load and hardware. The benchmark is end-to-end through the router, so router serialization may constrain scaling.

## 6. Results — fill with observed measurements
**Do not submit this section as measured results until the benchmark has actually run.** Copy the numerical results from `results/benchmark.csv` and attach `results/throughput.png`, `results/latency_mean.png`, and `results/latency_p95.png`.

| Active nodes | Throughput (ops/s) | Mean latency (ms) | P95 latency (ms) | Errors |
|---|---:|---:|---:|---:|
| 1 | TBD | TBD | TBD | TBD |
| 2 | TBD | TBD | TBD | TBD |
| 3 | TBD | TBD | TBD | TBD |

For each metric, calculate mean across the three repeats. Throughput speedup = throughput(N)/throughput(1). Explain whether improvements are linear, sublinear, flat, or negative. Report actual observations, not assumed improvements.

## 7. Challenges and tradeoffs
- **Consistent routing:** deterministic SHA-256 avoids Python's randomized built-in `hash()`.
- **Skew:** 128 virtual nodes reduce uneven key ownership.
- **Reconfiguration:** copying before switching membership avoids routing to missing data.
- **SQLite writes:** write locks and per-operation connections preserve simple single-process correctness, but can limit throughput.
- **Router bottleneck:** synchronous locking simplifies migrations and correctness, but limits parallelism during requests. In production use read/write coordination and multiple routers with shared membership.
- **Failure handling:** upstream failures return 503; there is no replication or automatic failover.

## 8. Reproducibility
Python 3.11; dependencies in `requirements.txt` and `requirements-dev.txt`; Docker Compose defines the deployment. Source files and test commands are documented in `README_HW3.md`. Capture Docker version, OS, CPU, memory, and workload settings when reporting measured results.

## 9. Limitations and future work
Current backend inventory endpoint is trusted only because backends are on the private Docker network; production deployments need authentication and network policy. No consensus, automatic node-health failover, replication, or cross-router synchronization is implemented. A failed cleanup may leave stale copies, but the router uses only the new owner. Node reconfiguration should be executed by a single administrator and all writes should enter via the router.
