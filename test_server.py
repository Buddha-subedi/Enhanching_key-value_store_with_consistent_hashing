"""Functional tests: run server.py first in another terminal."""
import requests

BASE = "http://127.0.0.1:8080/functional_test"

def check(response, status):
    assert response.status_code == status, f"Expected {status}: {response.status_code} {response.text}"
    return response.json()

assert check(requests.put(BASE, json={"value": "hello"}, timeout=300), 200)["value"] == "hello"
assert check(requests.get(BASE, timeout=300), 200)["value"] == "hello"
assert check(requests.put(BASE, json={"value": "updated"}, timeout=300), 200)["value"] == "updated"
assert check(requests.get(BASE, timeout=300), 200)["value"] == "updated"
check(requests.put(BASE, json={"value": 123}, timeout=300), 400)
check(requests.delete(BASE, timeout=300), 200)
check(requests.get(BASE, timeout=300), 404)
check(requests.delete(BASE, timeout=300), 404)
print("PASS: PUT, GET, UPDATE, DEL, validation and missing-key handling")
