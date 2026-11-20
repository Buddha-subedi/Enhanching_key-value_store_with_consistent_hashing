"""Deterministic SHA-256 consistent-hashing ring with virtual nodes."""
import bisect
import hashlib


def digest(value):
    return int.from_bytes(hashlib.sha256(value.encode('utf-8')).digest(), 'big')


class HashRing:
    def __init__(self, nodes, replicas=128):
        if replicas < 1 or len(set(nodes)) != len(nodes):
            raise ValueError('Replicas must be positive and node IDs unique')
        self.nodes = list(nodes)
        self.replicas = replicas
        positions = sorted((digest(f'{node}#{i}'), node) for node in nodes for i in range(replicas))
        self.positions = [x for x, _ in positions]
        self.owners = [n for _, n in positions]

    def owner(self, key):
        if not self.positions:
            raise ValueError('No active KV nodes')
        i = bisect.bisect_left(self.positions, digest(key)) % len(self.positions)
        return self.owners[i]
