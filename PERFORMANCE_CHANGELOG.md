# Concurrency and timeout update (November 2026)

- Router now uses a writer-preferring reader/writer lock. Ordinary GET/PUT/POST/DELETE requests can be forwarded concurrently, while membership migrations retain exclusive access until routing and cleanup finish. This is still a single-router coursework design, not distributed consensus.
- HTTP request timeouts are 300 seconds (five minutes) in router, benchmark clients and tests. SQLite busy timeout is also 300 seconds. **A 300-second timeout is per request, not a five-minute total benchmark limit.**
- Existing `results/benchmark.csv`, plots, `REPORT_HW3.md`, and recorded PowerShell history are **historical measurements from before this concurrency change**. Do not interpret them as measurements of the updated router.
- Rerun benchmarks and regenerate plots after starting the updated containers.

PowerShell:

```powershell
docker compose up -d --build
python -m pytest -q test_hash_ring.py test_integration_hw3.py test_concurrency.py
python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3
python plot_hw3.py
```

The five-minute timeout protects slow calls but does not cure deadlocks or guarantee performance gains. Membership changes intentionally pause ordinary operations to preserve migration consistency.
