# Follow-up verification evidence (user-shared PowerShell output)

These are observations copied from the user's November 20–21, 2026 interactive session, **not independently reproduced in the packaging environment**.

```text
python -m pytest -q test_hash_ring.py test_integration_hw3.py
.... [100%]
4 passed in 113.76s (0:01:53)

POST /_admin/membership {"nodes":["kv1","kv2","kv3"]}
{"active_nodes":["kv1","kv2","kv3"],"cleanup_errors":[],"moved":0}

GET /health
{"active_nodes":["kv1","kv2","kv3"],"status":"ok","virtual_nodes_per_store":128}

3000 PUT /hw3_test_key_N requests
Successful: 3000 | Failed: 0

GET /_admin/distribution
{"counts":{"kv1":986,"kv2":962,"kv3":1052},"total":3000}
```

Note: the user had not yet supplied a complete 3,000-key GET verification transcript. A separate `HW3_HISTORY_COMMANDS.md` provides commands to capture additional evidence.
