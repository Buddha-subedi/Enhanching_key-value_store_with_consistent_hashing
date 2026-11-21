# Assignment 3 — Distributed KV Store with Consistent Hashing

## 1. Objective
Extend the prior Flask/SQLite HTTP KV store to distribute keys across one, two, and three independent instances using consistent hashing, and compare end-to-end throughput and latency under identical workloads.

## 2. Baseline and architecture
The supplied Assignment 2 server (`server.py`) retains its SQLite database and CRUD API. A new Flask router (`router.py`) forwards requests to one of three backend instances (`kv1`, `kv2`, `kv3`). Each backend has its **own named Docker volume**, so the instances are separate partitions, not replicas. All external traffic enters through port 8000. Docker internal networking hides backend ports from the host.

## 3. Hashing algorithm
`hash_ring.py` hashes each node identifier and 128 virtual-node indices using SHA-256 and sorts these positions. A key is assigned to the first virtual node clockwise from SHA-256(key), wrapping at the end. Virtual nodes improve distribution across a small number of physical servers. When a node joins, only keys now assigned to that node should change ownership. This is tested using 10,000 synthetic keys.

## 4. Scaling and data integrity
The authenticated membership endpoint accepts `{"nodes":["kv1","kv2"]}`. It locks all router requests, inventories existing backend keys, copies keys to their new owners, verifies successful HTTP writes, switches the active ring, and cleans up stale copies. Existing data remains accessible across 1→2→3→2→1 membership transitions. Migration is intentionally synchronous and pauses traffic; for production, a distributed coordination service, transactional migration, streaming, authentication between services, and redundancy would be necessary. An unreachable backend returns an error; consistent hashing **does not provide fault tolerance or replication by itself**.

## 5. Experimental method and observed execution

The distributed deployment was built and started with `docker compose up -d --build`. Docker Compose reported successful creation of three backend containers (`kv1`, `kv2`, `kv3`), a router, three distinct named data volumes, and a private network. Development dependencies were installed/confirmed using `python -m pip install -r requirements-dev.txt`.

The **actual recorded** distributed benchmark command was:

```powershell
python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3
python plot_hw3.py
```

The benchmark tested 1, 2, and 3 active backend nodes, with 1,200 timed operations per repeat, 16 concurrent workers, and three repeats per configuration (10,800 successful timed operations in total). The implementation describes a default 80% read / 20% update workload with 128-byte values; the command did **not** explicitly override `--read-fraction`. The tests measure end-to-end requests through the router. Throughput is successful operations divided by elapsed time; reported latency statistics describe individual requests. The summary below is the **arithmetic mean of the three run-level metrics**, not a pooled request-level percentile.

The original benchmark transcript did not contain pytest output. In a later user-shared Windows PowerShell session, `python -m pytest -q test_hash_ring.py test_integration_hw3.py` reported **4 passed in 113.76s**. This is user-reported execution evidence, not a fresh independent execution in this review. Earlier standalone CRUD, concurrency, and volume persistence tests were completed separately.

## 6. Measured distributed results (November 20, 2026)

| Active nodes | Mean throughput (ops/s) | Mean latency (ms) | Mean P95 latency (ms) | Errors | Throughput vs. 1 node |
|---|---:|---:|---:|---:|---:|
| 1 | 95.61 | 167.17 | 386.94 | 0 | 1.000x |
| 2 | 97.54 | 162.77 | 384.97 | 0 | 1.020x |
| 3 | 82.94 | 197.45 | 447.69 | 0 | 0.867x |

All nine distributed benchmark repetitions reported 1,200 successful operations and **zero errors**. Two nodes gave the highest average throughput and lowest average latency, but the improvement over one node was small. Three nodes performed worse on average under this workload. These are measurements from one host, not evidence that adding nodes always decreases performance.

### Per-repeat measurements

| Nodes | Repeat | Successful | Errors | Throughput (ops/s) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1200 | 0 | 99.751 | 158.984 | 123.986 | 378.458 | 628.119 |
| 1 | 2 | 1200 | 0 | 102.799 | 154.499 | 122.789 | 380.724 | 621.781 |
| 1 | 3 | 1200 | 0 | 84.283 | 188.033 | 152.101 | 401.634 | 639.703 |
| 2 | 1 | 1200 | 0 | 95.907 | 165.522 | 124.473 | 386.688 | 606.313 |
| 2 | 2 | 1200 | 0 | 98.105 | 161.699 | 125.982 | 362.489 | 597.184 |
| 2 | 3 | 1200 | 0 | 98.606 | 161.089 | 131.293 | 405.736 | 640.278 |
| 3 | 1 | 1200 | 0 | 63.876 | 248.840 | 217.329 | 574.633 | 871.781 |
| 3 | 2 | 1200 | 0 | 89.942 | 176.692 | 152.856 | 395.728 | 606.694 |
| 3 | 3 | 1200 | 0 | 94.997 | 166.807 | 135.287 | 372.717 | 620.392 |

### Interpretation

- **1 → 2 nodes:** throughput changed by **+2.02%**, and mean latency changed by **-2.63%**.
- **1 → 3 nodes:** throughput changed by **-13.25%**, and mean latency changed by **+18.11%**.
- Three-node repeat 1 was notably slower (63.876 ops/s, mean latency 248.840 ms) than repeats 2 and 3 (89.942 and 94.997 ops/s), indicating run-to-run variability. Possible causes include resource contention, router overhead, or background activity; these were not independently measured.
- The benchmark demonstrates end-to-end performance under a fixed 16-worker workload, **not** storage balance, fault tolerance, replication, or multi-host horizontal scaling.

### Generated artifacts

The PowerShell transcript confirms that `plot_hw3.py` generated the following files locally:

- `results/benchmark.csv`
- `results/throughput.png`
- `results/latency_mean.png`
- `results/latency_p95.png`

If these PNG files are committed to GitHub, the following Markdown references will display the actual plots:

![Throughput by active backend count](results/throughput.png)
![Mean latency by active backend count](results/latency_mean.png)
![P95 latency by active backend count](results/latency_p95.png)

**Evidence boundary:** the uploaded ZIP contains `results/benchmark.csv` and the three PNG figures. The performance values are historical measurements, not rerun during this ZIP update.

## 7. Challenges and tradeoffs
- **Consistent routing:** deterministic SHA-256 avoids Python's randomized built-in `hash()`.
- **Skew:** 128 virtual nodes reduce uneven key ownership.
- **Reconfiguration:** copying before switching membership avoids routing to missing data.
- **SQLite writes:** write locks and per-operation connections preserve simple single-process correctness, but can limit throughput.
- **Router bottleneck:** synchronous locking simplifies migrations and correctness, but limits parallelism during requests. In production use read/write coordination and multiple routers with shared membership.
- **Failure handling:** upstream failures return 503; there is no replication or automatic failover.

## 8. Reproducibility and standalone validation

- **Environment recorded in the earlier PowerShell transcript:** Windows 10 (build 19045), Windows PowerShell 5.1, Python 3.11.9, Docker Engine/CLI 29.9.2, Docker Compose 5.6.1, Docker Desktop with WSL2 Linux backend, x86_64, **4 CPUs and 3.76 GiB memory allocated to Docker**. The Docker CPU/RAM values are Docker's available resources, not necessarily the host's full specifications.
- **Standalone CRUD test:** `python test_server.py` passed PUT, GET, UPDATE, DELETE, validation, and missing-key handling.
- **Standalone concurrency test:** `python test_concurrency.py` passed 60 concurrent PUTs and 30 concurrent DELETEs on one key.
- **Standalone performance test (not comparable to the distributed benchmark):** `python kv_bench.py` completed 300 SETs at 145.3 ops/s and 300 GETs at 180.0 ops/s, 600 successful operations overall at 160.8 ops/s. This used a different workload and must not be substituted for the 1-node distributed benchmark.
- **Persistence:** a `persist_check` value was retrieved successfully after removing and recreating the standalone container with the same `kv-data` volume. This is persistence across container recreation, **not** replica-based fault tolerance.
- **Distributed deployment:** `docker compose up -d --build` started router plus kv1/kv2/kv3; nine benchmark repetitions completed with zero reported errors.
- **Follow-up verification (user-reported):** 4 pytest tests passed; all three nodes active; 3,000 PUTs successful; physical key-count distribution totaled 3,000. Automatic node-failure recovery is not implemented.

To reproduce the distributed benchmark and its plots, use the commands in `README_HW3.md`.

## 9. Limitations and future work
Current backend inventory endpoint is trusted only because backends are on the private Docker network; production deployments need authentication and network policy. No consensus, automatic node-health failover, replication, or cross-router synchronization is implemented. A failed cleanup may leave stale copies, but the router uses only the new owner. Node reconfiguration should be executed by a single administrator and all writes should enter via the router.

## 10. Direct physical distribution verification (November 21, 2026 follow-up)

After setting membership to `kv1`, `kv2`, `kv3`, the router health endpoint reported three active stores and 128 virtual nodes per store. The user executed 3,000 distinct `PUT /hw3_test_key_N` requests through port 8000, reporting `Successful: 3000 | Failed: 0`. The authenticated `/_admin/distribution` endpoint then reported:

| Store | Keys | Share | Deviation from 1,000 ideal |
|---|---:|---:|---:|
| kv1 | 986 | 32.87% | -14 (-1.4%) |
| kv2 | 962 | 32.07% | -38 (-3.8%) |
| kv3 | 1,052 | 35.07% | +52 (+5.2%) |
| **Total** | **3,000** | **100%** | **0** |

This supports the requirement that keys are reasonably evenly distributed among three stores. The largest deviation from the ideal 1,000 keys is 5.2%. It does not demonstrate automatic failover, retrieval of all 3,000 keys, or improved three-node throughput. The counts and test outcome were supplied in chat from Windows PowerShell; see `results/validation_observations.md`.

## 11. Reproducible PowerShell evidence

Use `HW3_HISTORY_COMMANDS.md` to capture a fresh transcript showing startup, CRUD, 1→2→3 membership, 3,000-key distribution, retrieval, scale-down/up data preservation, tests, and the original benchmark artifacts. Running a new benchmark overwrites `results/benchmark.csv`; make a backup before doing so.
