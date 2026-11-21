"""HTTP gateway, membership control and stop-the-world safe key rebalancing.

Administrative membership updates require ROUTER_ADMIN_TOKEN. The router reader/writer lock
allows concurrent client requests while serializing migrations; do not run multiple routers without
shared coordination. This is a coursework single-router design, not consensus.
"""
import os
import threading
from contextlib import contextmanager
from collections import Counter
from urllib.parse import quote
import requests
from flask import Flask, jsonify, request
from hash_ring import HashRing

app = Flask(__name__)
NODE_URLS = {f'kv{i}': os.getenv(f'KV{i}_URL', f'http://127.0.0.1:{8080+i}') for i in (1,2,3)}
active = [f'kv{i}' for i in range(1, int(os.getenv('ACTIVE_NODES', '3'))+1)]
class ReaderWriterLock:
    """Writer-preferring lock: concurrent requests, exclusive membership changes."""
    def __init__(self):
        self.condition = threading.Condition(threading.Lock())
        self.readers = 0
        self.writer = False
        self.waiting_writers = 0

    @contextmanager
    def read(self):
        with self.condition:
            while self.writer or self.waiting_writers:
                self.condition.wait()
            self.readers += 1
        try:
            yield
        finally:
            with self.condition:
                self.readers -= 1
                if not self.readers:
                    self.condition.notify_all()

    @contextmanager
    def write(self):
        with self.condition:
            self.waiting_writers += 1
            try:
                while self.writer or self.readers:
                    self.condition.wait()
                self.writer = True
            finally:
                self.waiting_writers -= 1
        try:
            yield
        finally:
            with self.condition:
                self.writer = False
                self.condition.notify_all()

lock = ReaderWriterLock()
ring = HashRing(active)
TOKEN = os.getenv('ROUTER_ADMIN_TOKEN', 'local-dev-token')
TIMEOUT = float(os.getenv('UPSTREAM_TIMEOUT', '300'))


def upstream(node, method, key, payload=None):
    return requests.request(method, NODE_URLS[node] + '/' + quote(key, safe=''), json=payload, timeout=TIMEOUT)


def node_items(node):
    response = requests.get(NODE_URLS[node] + '/_internal/items', timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()['items']


def admin_ok():
    return request.headers.get('X-Admin-Token') == TOKEN


@app.get('/health')
def health():
    with lock.read():
        return jsonify(status='ok', active_nodes=active, virtual_nodes_per_store=ring.replicas)


@app.get('/_admin/distribution')
def distribution():
    if not admin_ok():
        return jsonify(error='Unauthorized'), 401
    with lock.read():
        try:
            counts = {n: len(node_items(n)) for n in active}
            return jsonify(counts=counts, total=sum(counts.values()))
        except requests.RequestException as exc:
            return jsonify(error=str(exc)), 502


@app.post('/_admin/membership')
def membership():
    global active, ring
    if not admin_ok():
        return jsonify(error='Unauthorized'), 401
    body = request.get_json(silent=True) or {}
    target = body.get('nodes')
    if not isinstance(target, list) or not target or len(target) != len(set(target)) or any(n not in NODE_URLS for n in target):
        return jsonify(error='nodes must be a nonempty unique list of kv1, kv2, kv3'), 400
    with lock.write():
        if set(target) == set(active):
            return jsonify(active_nodes=active, moved=0)
        next_ring = HashRing(target)
        # Stage copies first; verify writes before removing originals. During
        # failure no source keys are deleted, and the old ring remains active.
        try:
            inventory = {n: node_items(n) for n in active}
            # Also include any pre-existing keys on target nodes to support
            # restarting after a partial migration.
            for n in target:
                if n not in inventory:
                    inventory[n] = node_items(n)
            keys = {}
            for n in active + [n for n in target if n not in active]:
                keys.update(inventory[n])
            moved = 0
            for key, value in keys.items():
                owner = next_ring.owner(key)
                if inventory[owner].get(key) != value:
                    r = upstream(owner, 'PUT', key, {'value': value})
                    r.raise_for_status()
                    moved += 1
            # Commit routing before cleanup. A failed cleanup can leave
            # redundant copies, but never makes the routed key disappear.
            old_active = active
            active = list(target)
            ring = next_ring
            cleanup_errors = []
            for n in set(old_active) | set(target):
                for key in inventory[n]:
                    if next_ring.owner(key) != n:
                        try:
                            upstream(n, 'DELETE', key).raise_for_status()
                        except requests.RequestException as exc:
                            cleanup_errors.append(f'{n}:{key}: {exc}')
            return jsonify(active_nodes=active, moved=moved, cleanup_errors=cleanup_errors)
        except requests.RequestException as exc:
            return jsonify(error='Migration failed; old membership retained', detail=str(exc)), 502


@app.route('/<key>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def proxy(key):
    if key.startswith('_admin') or key == 'health' or key.startswith('_internal'):
        return jsonify(error='Reserved key prefix'), 400
    with lock.read():
        node = ring.owner(key)
        try:
            response = upstream(node, request.method, key, request.get_json(silent=True) if request.method in ('PUT','POST') else None)
            return (response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'application/json'), 'X-KV-Node': node})
        except requests.RequestException:
            return jsonify(error='KV node unavailable', node=node), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('ROUTER_PORT','8000')), threaded=True)
