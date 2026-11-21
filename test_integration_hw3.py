"""Requires running docker compose up -d --build."""
import os
import uuid
import requests

BASE = os.getenv('ROUTER_URL','http://localhost:8000')
HEADERS = {'X-Admin-Token': os.getenv('ROUTER_ADMIN_TOKEN','local-dev-token')}

def test_membership_and_crud():
    prefix = 'hw3-' + uuid.uuid4().hex
    keys = [f'{prefix}-{i}' for i in range(90)]
    try:
        for n in (1,2,3,2,1):
            r = requests.post(BASE+'/_admin/membership',json={'nodes':[f'kv{i}' for i in range(1,n+1)]},headers=HEADERS,timeout=300)
            assert r.status_code == 200, r.text
            for k in keys:
                if n == 1:
                    assert requests.put(BASE+'/'+k,json={'value':k},timeout=300).status_code == 200
                r = requests.get(BASE+'/'+k,timeout=300)
                assert r.status_code == 200 and r.json()['value'] == k
            r = requests.get(BASE+'/_admin/distribution',headers=HEADERS,timeout=300)
            assert r.status_code == 200
            assert sum(r.json()['counts'].values()) >= len(keys)
    finally:
        for k in keys:
            requests.delete(BASE+'/'+k,timeout=300)
