"""Streamlink owns network access; PyAV consumes the same bounded OS pipe."""
import subprocess
import sys
import threading
from .sources import validate_source


class StreamCapture:
    def __init__(self):
        self._lock = threading.Lock()
        self._process = None

    def start(self, url, quality, stop):
        validate_source(url)
        if quality == "auto":
            quality = "best"
        if not isinstance(quality, str) or not quality or len(quality) > 64 or quality.startswith('-'):
            raise ValueError('Invalid stream quality')
        with self._lock:
            if stop.is_set():
                return None
            self._process = subprocess.Popen(
                [sys.executable, '-m', 'streamlink', '--stdout',
                 '--stream-timeout', '15', '--', url, quality],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, shell=False)
            return self._process.stdout

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
                if process.stdout is not None:
                    process.stdout.close()
