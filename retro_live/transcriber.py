"""Bridge bounded PCM jobs to a cancellable process with bounded retries."""
import logging
import multiprocessing as mp
import time
from queue import Empty, Full
from .events import Event
from .performance import MONITOR
from .whisper_process import run_engine
from .whisper_policy import INFERENCE_HARD_LIMIT

LOG = logging.getLogger('retrocast.application')


def publish(events, event, stop, player):
    while not stop.is_set() and not player.stop_flag.is_set():
        try:
            events.put(event, timeout=.2)
            return True
        except Full:
            continue
    return False


class PlaybackWaitTimeout(TimeoutError):
    """Playback reached a pending block and exhausted its wait budget."""


def _receive(connection, process, stop, player, deadline=None, wait_window=None):
    waiting_since = None
    while not stop.is_set() and not player.stop_flag.is_set():
        now = time.monotonic()
        remaining = .05 if deadline is None else min(.05, deadline-now)
        if wait_window is not None:
            start, end, timeout = wait_window
            pos = player.position
            waiting = (player.priority == 'subtitle' and player.whisper_waiting
                       and pos is not None and start-.02 <= pos < end)
            if waiting:
                if waiting_since is None:
                    waiting_since = now
                if now-waiting_since >= timeout:
                    raise PlaybackWaitTimeout("Playback wait deadline")
                remaining = min(remaining, timeout-(now-waiting_since))
            else:
                waiting_since = None
        if remaining <= 0:
            raise TimeoutError('Whisper deadline')
        if connection.poll(remaining):
            return connection.recv()
        if not process.is_alive():
            raise RuntimeError('Whisper process exited')
    return None


class Engine:
    def __init__(self, config, stop, player):
        self.config, self.stop, self.player = config, stop, player
        self.process = self.parent = None

    def start(self, deadline):
        context = mp.get_context('spawn')
        self.parent, child = context.Pipe()
        self.process = context.Process(target=run_engine, args=(child, self.config), daemon=True)
        try:
            self.process.start()
        finally:
            child.close()
        LOG.info('whisper_engine_started pid=%s', self.process.pid)
        response = _receive(self.parent, self.process, self.stop, self.player, deadline)
        if response is None:
            return False
        if response[0] != 'ready':
            LOG.error('whisper_start_failed type=%s trace=%s', *response[1])
            raise RuntimeError('Whisper initialization failed')
        MONITOR.duration('ai.model_load', response[1]*1000)
        LOG.info('whisper_ready')
        return True

    def close(self):
        if self.parent is not None:
            self.parent.close()
            self.parent = None
        p, self.process = self.process, None
        if p is not None:
            if p.pid is not None:
                pid = p.pid
                if p.is_alive():
                    p.terminate()
                    p.join(.5)
                    if p.is_alive():
                        p.kill()
                p.join()
                LOG.info('whisper_engine_stopped pid=%s exit=%s', pid, p.exitcode)
            p.close()

    def infer(self, start, audio, deadline, wait_window=None):
        if self.process is None and not self.start(deadline):
            return None
        if time.monotonic() >= deadline:
            raise TimeoutError('Whisper deadline')
        self.parent.send((start, audio))
        return _receive(self.parent, self.process, self.stop, self.player, deadline, wait_window)


def transcribe(config, player, events, stop):
    engine = Engine(config, stop, player)
    jobs = player.jobs
    try:
        # Initial model load has its own bounded deadline (downloads may take longer).
        if not stop.is_set():
            try:
                engine.start(time.monotonic()+120)
            except Exception as exc:
                LOG.warning('whisper_initial_load_failed type=%s', type(exc).__name__)
                engine.close()
        while not stop.is_set() and not player.stop_flag.is_set():
            try:
                start, audio = jobs.get(timeout=.1)
            except Empty:
                if player._ended:
                    break
                continue
            try:
                if player.priority == "balanced":
                    (start, audio), dropped = jobs.newest((start, audio))
                    for old_start, old_audio in dropped:
                        player.discard_transcription(old_start, old_start+len(old_audio)/16000)
                        player.ai_dropped += 1
                        MONITOR.increment("ai.jobs_stale")
                        LOG.info("whisper_stale_discard pts=%.3f newest=%.3f", old_start, start)
                began = time.monotonic()
                duration = len(audio)/16000
                priority = player.priority
                policy = player.whisper_policy.effective(priority)
                budget = INFERENCE_HARD_LIMIT
                wait_window = (start, start+duration, policy.timeout) if priority == "subtitle" else None
                player.ai_policy = policy
                player.ai_active = start
                MONITOR.increment('ai.jobs_started')
                response = None
                attempts_used = 0
                for attempt in range(policy.retries+1):
                    if stop.is_set() or player.stop_flag.is_set():
                        return
                    player.ai_attempt = attempt+1
                    attempts_used = attempt+1
                    try:
                        if engine.process is None and not engine.start(time.monotonic()+120):
                            return
                        response = engine.infer(start, audio, time.monotonic()+budget, wait_window)
                        if response is None:
                            return
                        if response[0] == 'result':
                            break
                        LOG.warning('whisper_segment_failed pts=%.2f type=%s trace=%s', start, *response[1])
                    except Exception as exc:
                        LOG.warning('whisper_attempt_failed pts=%.2f attempt=%d type=%s hard_timeout=%.3f wait_timeout=%.1f', start, attempt+1, type(exc).__name__, budget, policy.playback_timeout(priority))
                        engine.close()
                    response = None
                    if player.priority != 'subtitle':
                        break
                    if attempt < policy.retries:
                        MONITOR.increment('ai.retries')
                        LOG.info('whisper_retry pts=%.2f attempt=%d', start, attempt+2)
                if response is None:
                    if not publish(events, Event('transcription_discarded', (start, start+duration)), stop, player):
                        return
                    MONITOR.increment('ai.jobs_expired')
                    LOG.warning('whisper_job_discarded pts=%.2f end=%.2f attempts=%d', start, start+duration, attempts_used)
                    continue
                cues, rejected = response[1]
                for cue in cues:
                    if not publish(events, Event('cue', cue), stop, player):
                        return
                if not publish(events, Event('transcription_complete', (start, start+duration)), stop, player):
                    return
                elapsed = time.monotonic()-began
                player.ai_last_completed = start+duration
                pos = player.position
                LOG.info('whisper_segment_complete pts=%.2f end=%.2f cues=%d rejected=%d elapsed=%.3f rtf=%.3f queue=%d playback=%s lead=%s', start, start+duration, len(cues), rejected, elapsed, elapsed/max(duration,.001), jobs.qsize(), pos, None if pos is None else round(start+duration-pos,3))
                MONITOR.increment('ai.jobs_completed')
                MONITOR.increment('ai.cues_emitted', len(cues))
                MONITOR.increment('ai.cues_rejected', rejected)
                MONITOR.duration('ai.inference', elapsed*1000)
                MONITOR.duration('ai.realtime_factor_x1000', elapsed/max(duration,.001)*1000)
            finally:
                player.ai_active = None
                player.ai_attempt = 0
                player.ai_policy = None
                jobs.task_done()
    except Exception as exc:
        if not stop.is_set() and not player.stop_flag.is_set():
            LOG.error('whisper_engine_failed type=%s', type(exc).__name__)
            if player.require_transcription:
                player.fail_transcription(type(exc).__name__)
    finally:
        engine.close()
