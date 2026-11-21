from hash_ring import HashRing

def test_deterministic():
    a = HashRing(['kv1','kv2','kv3'])
    b = HashRing(['kv1','kv2','kv3'])
    assert all(a.owner(str(k)) == b.owner(str(k)) for k in range(1000))

def test_minimal_remapping_on_add():
    a = HashRing(['kv1','kv2'])
    b = HashRing(['kv1','kv2','kv3'])
    keys = [str(i) for i in range(10000)]
    changed = [k for k in keys if a.owner(k) != b.owner(k)]
    assert changed
    assert all(b.owner(k) == 'kv3' for k in changed)
    assert .22 < len(changed)/len(keys) < .45

def test_balance():
    from collections import Counter
    ring = HashRing(['kv1','kv2','kv3'])
    counts = Counter(ring.owner(str(k)) for k in range(10000))
    assert all(.22 < counts[n]/10000 < .45 for n in ring.nodes)
