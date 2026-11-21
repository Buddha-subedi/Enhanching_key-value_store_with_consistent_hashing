"""Unit tests for concurrent forwarding / exclusive migration synchronization."""
import threading
import time
from router import ReaderWriterLock

def test_parallel_readers():
    rw = ReaderWriterLock()
    entered = threading.Barrier(3, timeout=5)
    def reader():
        with rw.read():
            entered.wait()
    threads = [threading.Thread(target=reader) for _ in range(2)]
    for thread in threads: thread.start()
    entered.wait()
    for thread in threads: thread.join(timeout=5)
    assert all(not thread.is_alive() for thread in threads)

def test_writer_waits_for_reader():
    rw = ReaderWriterLock()
    acquired = threading.Event()
    def writer():
        with rw.write(): acquired.set()
    with rw.read():
        thread = threading.Thread(target=writer)
        thread.start()
        assert not acquired.wait(0.1)
    thread.join(timeout=5)
    assert acquired.is_set()
