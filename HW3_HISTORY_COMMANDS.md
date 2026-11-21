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

## A. Start the single complete transcript

```powershell
Start-Transcript -Path ".\HW3_Complete_PowerShell_History.txt" -Force
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

## E. Physical key distribution (3,000 keys)

This uses the correct endpoint `PUT /<key>` (NOT `/kv/<key>`). If you already inserted these keys, the PUTs update them and counts should remain at 3,000 for this key set. Other existing keys may raise the overall count.

```powershell
$success=0; $failed=0; 1..3000 | ForEach-Object { $k="hw3_test_key_$_"; $body=@{value="test_value_$_"} | ConvertTo-Json -Compress; try { Invoke-RestMethod -Uri "http://localhost:8000/$k" -Method Put -ContentType "application/json" -Body $body -ErrorAction Stop | Out-Null; $success++ } catch { $failed++; Write-Host "FAILED: $k - $_" } }; Write-Host "Successful: $success | Failed: $failed"
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"} | ConvertTo-Json -Depth 10
```

```powershell
$good=0; $bad=0; 1..3000 | ForEach-Object { $k="hw3_test_key_$_"; try { $r=Invoke-RestMethod -Uri "http://localhost:8000/$k" -Method Get -ErrorAction Stop; if ($r.value -eq "test_value_$_") { $good++ } else { $bad++; Write-Host "MISMATCH: $k" } } catch { $bad++; Write-Host "FAILED GET: $k - $_" } }; Write-Host "Readable and correct: $good | Errors: $bad"
```

## F. Demonstrate safe reconfiguration while preserving keys

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"} | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_test_key_3000" -Method Get | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/hw3_test_key_3000" -Method Get | ConvertTo-Json -Depth 10
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/distribution" -Headers @{"X-Admin-Token"="local-dev-token"} | ConvertTo-Json -Depth 10
```

## G. Tests

```powershell
python -m pip install -r requirements-dev.txt
```

```powershell
python -m pytest -q test_hash_ring.py test_integration_hw3.py
```

**Note:** The integration test ends with one active node, so re-enable all three afterward:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/_admin/membership" -Method Post -ContentType "application/json" -Headers @{"X-Admin-Token"="local-dev-token"} -Body '{"nodes":["kv1","kv2","kv3"]}' | ConvertTo-Json -Depth 10
```

## H. Throughput and latency: 1, 2, and 3 stores

**Existing benchmark data is already included in this ZIP.** If you want a completely new run in the transcript, first preserve historical files, because `benchmark_hw3.py` overwrites `results/benchmark.csv` and `plot_hw3.py` overwrites the PNGs.

```powershell
New-Item -ItemType Directory -Force -Path ".\results\historical_backup" | Out-Null; Copy-Item ".\results\benchmark.csv" ".\results\historical_backup\benchmark.csv" -Force; Copy-Item ".\results\*.png" ".\results\historical_backup\" -Force
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

The fresh benchmark results may differ from the historical report. If so, **update the report to match the new CSV** rather than presenting old numbers as new results.

## I. Stop recording and preserve the history

```powershell
Stop-Transcript
```

Now upload `HW3_Complete_PowerShell_History.txt` and `results/benchmark.csv` to ChatGPT for the final evidence review and report synchronization. The transcript includes actual commands and their output; PowerShell `Start-Transcript` does not retroactively capture commands run before it was started.
