"""Bounded asynchronous Streamlink availability checks; no media downloads."""
import json
import logging
import queue
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse
from .sources import validate_source
from .performance import MONITOR

LOG = logging.getLogger('retrocast.application')
WORKERS = 3
CAPACITY = 30
PROBE_TIMEOUT = 8
TTL = 60
ERROR_TTL = 20


def probe(url):
    try:
        validate_source(url)
        parsed = urlparse(url)
        # History must not send credential-bearing or arbitrary query strings.
        import re
        if parsed.query and not (parsed.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com') and re.fullmatch(r'v=[A-Za-z0-9_-]{11}', parsed.query)):
            return 'unknown', 'unsafe_query'
        result = subprocess.run(
            [sys.executable, '-m', 'streamlink', '--no-config', '--json', '--loglevel', 'error', '--', url],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=PROBE_TIMEOUT, shell=False)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if isinstance(data, dict) and isinstance(data.get('streams'), dict):
                return ('online', 'streams_found') if data['streams'] else ('offline', 'no_streams')
        diagnostic = (result.stderr + result.stdout).decode('utf-8', errors='replace').lower()
        if any(s in diagnostic for s in ('no playable streams', 'no streams found', 'is offline', 'channel does not exist', 'video unavailable', '404 client error')):
            return 'offline', 'unavailable'
        return 'unknown', 'probe_failed'
    except subprocess.TimeoutExpired:
        return 'unknown', 'timeout'
    except (ValueError, OSError, TypeError):
        return 'unknown', 'invalid_or_failed'


class HistoryStatus:
    """Main thread owns cache/pending; workers communicate only via queues."""
    def __init__(self, checker=probe, clock=time.monotonic):
        self.checker = checker
        self.clock = clock
        self.cache = {}
        self.pending = set()
        self.jobs = queue.Queue(CAPACITY)
        self.results = queue.Queue(CAPACITY)
        self.stop = threading.Event()
        self.workers = []

    def _start(self):
        if self.workers:
            return
        for i in range(WORKERS):
            worker = threading.Thread(target=self._worker, name=f'history-status-{i}', daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker(self):
        while not self.stop.is_set():
            try:
                url = self.jobs.get(timeout=.2)
            except queue.Empty:
                continue
            if self.stop.is_set():
                return
            started = time.monotonic()
            try:
                state, reason = self.checker(url)
            except Exception:
                state, reason = 'unknown', 'worker_failed'
            elapsed = time.monotonic() - started
            MONITOR.duration('history.probe', elapsed * 1000)
            MONITOR.increment('history.' + state)
            LOG.info('history_probe state=%s reason=%s elapsed_ms=%.1f', state, reason, elapsed*1000)
            if not self.stop.is_set():
                self.results.put_nowait((url, state))

    def request(self, urls, force=False):
        if self.stop.is_set():
            return
        now = self.clock()
        self._start()
        scheduled = False
        for url in urls:
            entry = self.cache.get(url)
            if url in self.pending or (not force and entry and entry[1] > now):
                continue
            if len(self.pending) >= CAPACITY:
                break
            self.pending.add(url)
            self.jobs.put_nowait(url)
            scheduled = True
        return scheduled

    def poll(self, history, visible=False):
        changed = False
        now = self.clock()
        for _ in range(CAPACITY):
            try:
                url, state = self.results.get_nowait()
            except queue.Empty:
                break
            self.pending.discard(url)
            if url in history:
                self.cache[url] = (state, now + (ERROR_TTL if state == 'unknown' else TTL))
            changed = True
        return changed

    def cancel_queued(self):
        """Cancel jobs not yet started; running probes finish within their timeout."""
        while True:
            try:
                url = self.jobs.get_nowait()
            except queue.Empty:
                break
            self.pending.discard(url)

    def state(self, url):
        if url in self.pending:
            return 'checking'
        entry = self.cache.get(url)
        return entry[0] if entry else 'unknown'

    def prune(self, history):
        allowed = set(history)
        for url in tuple(self.cache):
            if url not in allowed:
                del self.cache[url]

    def close(self):
        self.stop.set()
        self.cancel_queued()
