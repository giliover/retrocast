from .ring import Ring
from pathlib import Path
from queue import Queue, Empty
from dataclasses import replace
import logging
from .sources import validate_source
LOG = logging.getLogger("retrocast.application")
from threading import Event, Thread
from .config import Config
from .processes import ProcessManager
from .transcriber import transcribe
from .player import VideoPlayer

class Session:
    def __init__(self):
        self.config = Config()
        self.events = Queue(maxsize=256)
        self.stop = Event()
        self.processes = ProcessManager()
        self.video = VideoPlayer()
        self.lines = Ring(2000)
        self.cues = {}
        self.caption = ""
        self.status = 'PRONTO'
        self.running = False
        self.thread = None

    def start(self):
        if not self.config.url.strip():
            self.status = 'INSIRA UMA URL'
            return
        # WATCH always completes STOP before creating another capture.
        if not self.close(save=False):
            raise RuntimeError("Previous stream is still stopping; try again shortly")
        validate_source(self.config.url)
        self.events = Queue(maxsize=256)
        self.stop = Event()
        self.processes = ProcessManager()
        self.lines.clear()
        self.cues.clear()
        self.caption = ""
        self.status = 'CONECTANDO...'
        self.running = True
        self.video.start(self.config.url, self.config.quality, self.config.delay)
        LOG.info("session_started delay=%d", self.config.delay)
        self.thread = Thread(target=transcribe, args=(replace(self.config), self.video, self.events, self.stop), daemon=True)
        self.thread.start()

    def poll(self):
        changed = False
        for _ in range(100):
            try: event = self.events.get_nowait()
            except Empty: break
            if event.kind == 'cue':
                start, end, text = event.value
                self.lines.append(text)
                changed = True
                for slot in range(int(start*10), min(int(end*10)+1, int(start*10)+300)):
                    self.cues[slot] = text
                    if len(self.cues) > 1400:
                        self.cues.pop(next(iter(self.cues)))
            elif event.kind == 'line':
                self.lines.append(event.value)
                changed = True
            else:
                self.status = ('ERRO: ' if event.kind == 'error' else '') + event.value
        pos = self.video.position if self.running else None
        caption = self.cues.get(int(pos*10), '') if pos is not None else ''
        if caption != self.caption:
            self.caption = caption
            changed = True
        if self.running and self.video._ended and not (self.video.worker and self.video.worker.is_alive()):
            self.running = False
            self.caption = ""
            self.status = "ENDED"
        if self.running and pos is None and not self.video.error and not self.status.startswith("ERRO:"):
            self.status = f'BUFFER: {max(0,self.video.latest):.0f}/{self.config.delay}s'
        elif self.running and not self.video.error and not self.status.startswith("ERRO:"):
            self.status = f'PLAYING | BUFFER {max(0,self.video.latest-(pos or 0)):.0f}s'
        if self.video.error and (self.running or self.status == "ENDED"):
            self.status = 'VIDEO: ' + self.video.error
        return changed

    def save(self):
        path = Path(self.config.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(self.lines) + ('\n' if self.lines else ''), encoding='utf-8')
        self.status = 'SALVO: ' + str(path)

    def close(self, save=True):
        """Stop both pipelines. Never start a new one while an old worker lives."""
        self.stop.set()
        self.processes.close()  # Unblocks ffmpeg/stdout reads in transcription.
        video_stopped = self.video.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=.1)
        transcription_stopped = not (self.thread and self.thread.is_alive())
        if transcription_stopped:
            self.thread = None
        self.running = False
        self.caption = ""
        LOG.info("session_stopped complete=%s", video_stopped and transcription_stopped)
        # Old status and subtitle events must not reappear after STOP.
        self.events = Queue(maxsize=256)
        self.status = 'STOPPED' if video_stopped and transcription_stopped else 'STOPPING...'
        if save and self.config.autosave and self.lines:
            self.save()
        return video_stopped and transcription_stopped
