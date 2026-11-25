"""Streamlink owns network access; PyAV consumes the same bounded OS pipe."""
import logging
import subprocess
import sys
import threading
from .sources import validate_source


LOG = logging.getLogger('retrocast.application')


def classify_stderr(line):
    """Only emit fixed categories; upstream diagnostics can contain credentials."""
    line = line.lower()
    rules = (
        (('no module named',), 'module_missing'),
        (('unrecognized arguments', 'invalid choice', 'usage:'), 'cli_arguments'),
        (('no playable streams', 'no streams found', 'offline'), 'stream_unavailable'),
        (('not available', 'available streams:'), 'quality_or_stream_unavailable'),
        (('403', '401', 'unauthorized', 'forbidden', 'authentication', 'login'), 'access_denied'),
        (('429', 'too many requests'), 'rate_limited'),
        (('certificate', 'ssl', 'tls'), 'tls_error'),
        (('timeout', 'timed out'), 'timeout'),
        (('connection', 'network', 'resolve host'), 'network_error'),
        (('no plugin', 'pluginerror'), 'plugin_error'),
        (('ffmpeg',), 'ffmpeg_error'),
        (('error', 'exception', 'traceback'), 'other_error'),
    )
    for needles, category in rules:
        if any(needle in line for needle in needles):
            return category
    return None


class StreamCapture:
    def __init__(self):
        self._lock = threading.Lock()
        self._process = None
        self._stderr_thread = None

    def start(self, url, quality, stop):
        validate_source(url)
        if quality == "auto":
            quality = "best"
        if not isinstance(quality, str) or not quality or len(quality) > 64 or quality.startswith('-'):
            raise ValueError('Invalid stream quality')
        if quality not in {'best', 'worst', '1080p', '720p', '480p', '360p'}:
            raise ValueError('Invalid stream quality')
        selection = quality if quality in {'best', 'worst'} else quality + ',best'
        with self._lock:
            if stop.is_set():
                return None
            self._process = subprocess.Popen(
                [sys.executable, '-m', 'streamlink', '--stdout',
                 '--loglevel', 'warning', '--stream-timeout', '15', '--', url, selection],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=False)
            self._stderr_thread = threading.Thread(target=self._drain_stderr, args=(self._process.stderr,), daemon=True)
            self._stderr_thread.start()
            LOG.info("streamlink_started quality=%s", selection)
            return self._process.stdout

    @staticmethod
    def _drain_stderr(pipe):
        seen = set()
        try:
            while chunk := pipe.readline(4096):
                category = classify_stderr(chunk.decode('utf-8', errors='replace'))
                if category and category not in seen:
                    seen.add(category)
                    LOG.warning('streamlink_diagnostic category=%s', category)
        finally:
            pipe.close()

    def returncode(self):
        with self._lock:
            return self._process.poll() if self._process else None

    def terminate(self):
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    self._process.terminate()
                except ProcessLookupError:
                    pass

    def close(self):
        self.terminate()
        with self._lock:
            process = self._process
        if process is not None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            finally:
                if self._stderr_thread is not None:
                    self._stderr_thread.join(timeout=2)
                LOG.info("streamlink_ended exit=%s", process.returncode)
                if process.stdout is not None:
                    process.stdout.close()
