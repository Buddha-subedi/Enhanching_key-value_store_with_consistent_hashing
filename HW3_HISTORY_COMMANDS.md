# HW3 — Complete PowerShell evidence capture (Windows)

**Important:** Run commands **one at a time**, in order. Each fenced command is a **single line** that can be pasted into Windows PowerShell. This produces a fresh, honest execution transcript, not a fabricated history. Do not paste the example expected outputs into the transcript.

## Before starting

Open Windows PowerShell in the **extracted project folder containing `compose.yaml`, `router.py`, and `benchmark_hw3.py`**. Check the current folder:

```powershell
Get-Location
```

```powershell
Test-Path .\compose.yaml
```

The second command must print `True`. If not, change into the actual extracted project folder before proceeding. **Do not use `docker compose down -v`**; it deletes data volumes. The following commands intentionally insert test data.

## A. Start or resume the single complete transcript

```powershell
Start-Transcript -Path ".\HW3_Complete_PowerShell_History.txt" -Append
```

```powershell
Get-Date -Format o
```

```powershell
python --version
```

```powershell
docker --version
```

```powershell
docker compose version
```

```powershell
docker info --format 'CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}'
```

## B. Environment and containerization

```powershell
docker compose config --services
```

```powershell
docker compose up -d --build
```

```powershell
docker compose ps
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 10
```

If the router is not yet ready, wait a few seconds and repeat the health command. All three containers can be running even when only one store is active in the ring.

## C. Functional CRUD test (router, one active store)

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Put -ContentType "application/json" -Body '{"value":"original"}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Get | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Put -ContentType "application/json" -Body '{"value":"updated"}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Get | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Delete | ConvertTo-Json -Depth 10
```

Verify that the deleted CRUD key returns HTTP 404 (expected behavior, not a failure):

```powershell
try { Invoke-RestMethod -Uri "http://localhost:8000/hw3_history_crud" -Method Get -ErrorAction Stop | Out-Null; Write-Host "FAIL: deleted CRUD key still exists" } catch { if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { Write-Host "PASS: deleted CRUD key returns HTTP 404" } else { Write-Host "FAIL: unexpected retrieval error: $_" } }
```

## D. Consistent hashing: 1 → 2 → 3 active stores

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 10
```

## E. Automated tests — BEFORE the 3,000-key workload


Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run unit tests (does not require membership migration):

```powershell
python -m pytest -q test_hash_ring.py
```

**Only on a fresh, isolated, empty test deployment**, run integration tests and record their actual outcome:

```powershell
python -m pytest -q test_integration_hw3.py
```

Verify the membership and test results before continuing. If the test fails, record the error and fix the underlying problem; do not proceed as if it passed.

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 10
```

Restore three active nodes after a *successful* integration test on the empty deployment:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

## F. Physical key distribution (3,000 keys) — REQUIRED BEFORE MIGRATION

**Run this section completely before Section G.** A newly created Docker Compose project normally has empty data volumes. A previous run in another project folder does not populate this one. The correct key endpoint is `/<key>` (NOT `/kv/<key>`).

First ensure that all three stores are ACTIVE, not merely running:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

Insert or overwrite the 3,000 uniquely named test keys:

```powershell
$success=0; $failed=0; 1..3000 | ForEach-Object { $k="hw3_test_key_$_"; $body=@{value="test_value_$_"} | ConvertTo-Json -Compress; try { Invoke-RestMethod -Uri "http://localhost:8000/$k" -Method Put -ContentType "application/json" -Body $body -ErrorAction Stop | Out-Null; $success++ } catch { $failed++; Write-Host "FAILED PUT: $k - $_" } }; Write-Host "Inserted: $success | Errors: $failed"; if ($failed -gt 0 -or $success -ne 3000) { throw "STOP: insertion incomplete; do not proceed to migration" }
```

Check the physical counts on the three ACTIVE stores:

```powershell
$d=Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"}; $d | ConvertTo-Json -Depth 10; if ($d.total -lt 3000 -or $d.counts.kv1 -le 0 -or $d.counts.kv2 -le 0 -or $d.counts.kv3 -le 0) { throw "STOP: expected at least 3000 keys distributed over all three stores" } else { Write-Host "PASS: all three stores hold keys; total=$($d.total)" }
```

Verify all 3,000 values through the router (may take several minutes):

```powershell
$good=0; $bad=0; 1..3000 | ForEach-Object { $i=$_; $k="hw3_test_key_$i"; try { $r=Invoke-RestMethod -Uri "http://localhost:8000/$k" -Method Get -ErrorAction Stop; if ($r.value -eq "test_value_$i") { $good++ } else { $bad++; Write-Host "MISMATCH: $k" } } catch { $bad++; Write-Host "FAILED GET: $k - $_" } }; Write-Host "Correct values: $good | Errors: $bad"; if ($bad -gt 0 -or $good -ne 3000) { throw "STOP: some keys are missing or incorrect; do not proceed to migration" }
```

**Proceed to G only if insertion succeeded, all three stores have keys, and all 3,000 GETs succeeded.** If a check fails, save its output and investigate rather than creating replacement keys during the migration test.

## G. Membership changes and data preservation (3 → 2 → 1 → 3)

The following steps intentionally check the same key at each membership size. A `FAIL` indicates a real retrieval/migration problem; do not hide it by inserting the missing key again. Run each command separately.

**G1 — Reduce to two stores:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2"]}' | ConvertTo-Json -Depth 10
```

```powershell
$d=Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"}; $d | ConvertTo-Json -Depth 10; if ($d.total -lt 3000 -or $d.counts.kv1 -le 0 -or $d.counts.kv2 -le 0) { throw "FAIL: keys missing after 3-to-2 migration" } else { Write-Host "PASS: 2-node distribution contains at least 3000 keys" }
```

```powershell
$good=0; $bad=0; 1,500,1000,2000,3000 | ForEach-Object { $i=$_; try { $r=Invoke-RestMethod -Uri "http://localhost:8000/hw3_test_key_$i" -Method Get -ErrorAction Stop; if ($r.value -eq "test_value_$i") { $good++; Write-Host "PASS: key $i" } else { $bad++; Write-Host "FAIL: wrong value for key $i" } } catch { $bad++; Write-Host "FAIL: key $i not readable: $_" } }; if ($bad -gt 0) { throw "STOP: failed 2-node key checks" }
```

**G2 — Reduce to one store:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1"]}' | ConvertTo-Json -Depth 10
```

```powershell
$d=Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"}; $d | ConvertTo-Json -Depth 10; if ($d.total -lt 3000 -or $d.counts.kv1 -lt 3000) { throw "FAIL: keys missing after 2-to-1 migration" } else { Write-Host "PASS: kv1 contains at least 3000 keys" }
```

```powershell
$good=0; $bad=0; 1,500,1000,2000,3000 | ForEach-Object { $i=$_; try { $r=Invoke-RestMethod -Uri "http://localhost:8000/hw3_test_key_$i" -Method Get -ErrorAction Stop; if ($r.value -eq "test_value_$i") { $good++; Write-Host "PASS: key $i" } else { $bad++; Write-Host "FAIL: wrong value for key $i" } } catch { $bad++; Write-Host "FAIL: key $i not readable: $_" } }; if ($bad -gt 0) { throw "STOP: failed 1-node key checks" }
```

**G3 — Restore three stores:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

```powershell
$d=Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"}; $d | ConvertTo-Json -Depth 10; if ($d.total -lt 3000 -or $d.counts.kv1 -le 0 -or $d.counts.kv2 -le 0 -or $d.counts.kv3 -le 0) { throw "FAIL: distribution after restoring 3 nodes" } else { Write-Host "PASS: keys present across all 3 stores" }
```

```powershell
$good=0; $bad=0; 1,500,1000,2000,3000 | ForEach-Object { $i=$_; try { $r=Invoke-RestMethod -Uri "http://localhost:8000/hw3_test_key_$i" -Method Get -ErrorAction Stop; if ($r.value -eq "test_value_$i") { $good++; Write-Host "PASS: key $i" } else { $bad++; Write-Host "FAIL: wrong value for key $i" } } catch { $bad++; Write-Host "FAIL: key $i not readable: $_" } }; if ($bad -gt 0) { throw "STOP: failed restored 3-node key checks" }
```

**Optional stronger verification:** Repeat the 3,000-key GET loop from Section F after G3 to check every key rather than five samples. The distribution endpoint measures counts, but only GET checks validate values.

## H. Throughput and latency: 1, 2, and 3 stores

**Existing benchmark data may already be present in your project.** If you want a completely new run in the transcript, first preserve historical files, because `benchmark_hw3.py` overwrites `results/benchmark.csv` and `plot_hw3.py` overwrites the PNGs.

```powershell
New-Item -ItemType Directory -Force -Path ".\results\historical_backup" | Out-Null; if (Test-Path ".\results\benchmark.csv") { Copy-Item ".\results\benchmark.csv" ".\results\historical_backup\benchmark.csv" -Force }; Get-ChildItem ".\results" -Filter "*.png" -ErrorAction SilentlyContinue | Copy-Item -Destination ".\results\historical_backup" -Force
```

```powershell
python benchmark_hw3.py --operations 1200 --workers 16 --repeats 3
```

```powershell
python plot_hw3.py
```

```powershell
Import-Csv ".\results\benchmark.csv" | Format-Table nodes,repeat,operations,successful,errors,throughput_ops_s,mean_ms,p95_ms -AutoSize
```

```powershell
Get-ChildItem ".\results\*.png" | Select-Object Name,Length
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 10
```

The benchmark should produce 1-, 2-, and 3-node measurements. Check for errors and ensure the CSV contains all three configurations. The fresh benchmark results may differ from the historical report. If so, **update the report to match the new CSV** rather than presenting old numbers as new results.

## I. Stop recording and preserve the history

**If you are resuming a previous transcript:** `-Append` preserves earlier evidence, including earlier mistakes. Do not delete or rewrite real failures. If any test fails, resolve it and record a successful rerun, with a brief explanation in the report. A new Docker Compose project has separate volumes, so old keys may not exist in the new deployment.


```powershell
Stop-Transcript
```




## Note on the November 21 failed run

The existing transcript is authentic evidence: 3,000 keys were distributed (986/962/1052), verified by 3,000 GETs, and migrated successfully, but the later integration test failed with `requests.exceptions.ReadTimeout` on a membership POST. Preserve that result in the original transcript and document any subsequent successful isolated rerun separately. Do not erase failures from recorded history.
