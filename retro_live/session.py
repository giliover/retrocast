from collections import deque
from pathlib import Path
from queue import Queue, Empty
from threading import Event, Thread
from .config import Config
from .processes import ProcessManager
from .transcriber import transcribe
from .player import VideoPlayer

class Session:
    def __init__(self):
        self.config = Config()
        self.events = Queue()
        self.stop = Event()
        self.processes = ProcessManager()
        self.video = VideoPlayer()
        self.lines = deque(maxlen=2000)
        self.status = 'PRONTO'
        self.running = False
        self.thread = None

    def start(self):
        if not self.config.url.strip():
            self.status = 'INSIRA UMA URL'
            return
        self.close(save=False)
        ProcessManager.check()
        self.events = Queue()
        self.stop = Event()
        self.processes = ProcessManager()
        self.lines.clear()
        self.status = 'CONECTANDO...'
        self.running = True
        self.video.start(self.config.url, self.config.quality)
        self.thread = Thread(target=transcribe, args=(self.config, self.processes, self.events, self.stop), daemon=True)
        self.thread.start()

    def poll(self):
        changed = False
        for _ in range(100):
            try: event = self.events.get_nowait()
            except Empty: break
            if event.kind == 'line':
                self.lines.append(event.value)
                changed = True
            else:
                self.status = ('ERRO: ' if event.kind == 'error' else '') + event.value
        if self.video.error:
            self.status = 'VIDEO: ' + self.video.error
        return changed

    def save(self):
        path = Path(self.config.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(self.lines) + ('\n' if self.lines else ''), encoding='utf-8')
        self.status = 'SALVO: ' + str(path)

    def close(self, save=True):
        self.stop.set()
        self.processes.close()
        self.video.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.running = False
        if save and self.config.autosave and self.lines:
            self.save()
