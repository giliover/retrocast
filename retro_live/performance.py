"""Thread-safe, low-overhead performance instrumentation (stdlib only)."""
from collections import defaultdict
from pathlib import Path
from threading import Lock
import logging
import os
import time

class PerformanceMonitor:
    def __init__(self):
        self.lock = Lock()
        self.samples = defaultdict(lambda: [0, 0.0, 0.0])  # count, total ms, max ms
        self.counts = defaultdict(int)
        self.started = time.monotonic()
        self.last_report = self.started
        log_dir = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'retrocast'
        log_dir.mkdir(parents=True, exist_ok=True)
        self.path = log_dir/'performance.log'
        self.logger = logging.getLogger('retrocast.performance')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        if not self.logger.handlers:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(self.path, maxBytes=3_000_000, backupCount=3, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
            self.logger.addHandler(handler)

    def duration(self, name, milliseconds):
        with self.lock:
            s = self.samples[name]
            s[0] += 1
            s[1] += milliseconds
            s[2] = max(s[2], milliseconds)

    def increment(self, name, amount=1):
        with self.lock:
            self.counts[name] += amount

    def snapshot(self, reset=False):
        with self.lock:
            metrics = {k: {'count': v[0], 'avg_ms': round(v[1]/v[0], 2) if v[0] else 0, 'max_ms': round(v[2], 2)} for k,v in self.samples.items()}
            counters = dict(self.counts)
            if reset:
                self.samples.clear()
                self.counts.clear()
        return metrics, counters

    def report_if_due(self, seconds=5):
        now = time.monotonic()
        if now-self.last_report < seconds:
            return
        self.last_report = now
        metrics, counts = self.snapshot(reset=True)
        self.logger.info('interval=%.1fs timings=%s counters=%s', seconds, metrics, counts)
        return metrics, counts

MONITOR = PerformanceMonitor()

def measure(name):
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *exc):
            MONITOR.duration(name, (time.perf_counter()-self.start)*1000)
    return Timer()
