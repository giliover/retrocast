import shutil
import importlib.util
import sys
import subprocess
import threading

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.lock = threading.Lock()

    @staticmethod
    def check():
        missing = ([] if importlib.util.find_spec('streamlink') else ['streamlink (venv)']) + ([] if shutil.which('ffmpeg') else ['ffmpeg'])
        if missing:
            raise RuntimeError('Comandos ausentes: ' + ', '.join(missing))

    def start(self, cmd, **kwargs):
        # Always execute Streamlink from the same interpreter as RetroCast.
        if cmd and cmd[0] == 'streamlink':
            cmd = [sys.executable, '-m', 'streamlink', *cmd[1:]]
        proc = subprocess.Popen(cmd, **kwargs)
        with self.lock:
            self.processes.append(proc)
        return proc

    def close(self):
        with self.lock:
            procs = list(reversed(self.processes))
            self.processes.clear()
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
