"""Bridge a bounded PCM queue to a cancellable, isolated Whisper process."""
import logging
import multiprocessing as mp
import time
from queue import Empty, Full
from .events import Event
from .performance import MONITOR
from .whisper_process import run_engine

LOG = logging.getLogger('retrocast.application')


def publish(events, event, stop, player):
    while not stop.is_set() and not player.stop_flag.is_set():
        try:
            events.put(event, timeout=.2)
            return True
        except Full:
            continue
    return False


def _receive(connection, process, stop, player):
    while not stop.is_set() and not player.stop_flag.is_set():
        if connection.poll(.05):
            return connection.recv()
        if not process.is_alive():
            raise RuntimeError('Whisper process exited')
    return None


def transcribe(config, player, events, stop):
    context = mp.get_context('spawn')
    parent, child = context.Pipe()
    process = context.Process(target=run_engine, args=(child, config), daemon=True)
    jobs = player.jobs
    try:
        if stop.is_set():
            return
        process.start()
        child.close()
        LOG.info('whisper_engine_started pid=%s', process.pid)
        response = _receive(parent, process, stop, player)
        if response is None:
            return
        if response[0] != 'ready':
            LOG.error('whisper_start_failed type=%s trace=%s', *response[1])
            raise RuntimeError('Whisper initialization failed')
        MONITOR.duration('ai.model_load', response[1]*1000)
        LOG.info('whisper_ready')
        while not stop.is_set() and not player.stop_flag.is_set():
            try:
                start, audio = jobs.get(timeout=.1)
            except Empty:
                if player._ended:
                    break
                continue
            try:
                if stop.is_set():
                    return
                began = time.monotonic()
                duration = len(audio)/16000
                player.ai_active = start
                MONITOR.increment('ai.jobs_started')
                parent.send((start, audio))
                response = _receive(parent, process, stop, player)
                if response is None:
                    return
                if response[0] == 'failed':
                    LOG.error('whisper_segment_failed pts=%.2f type=%s trace=%s', start, *response[1])
                    MONITOR.increment('ai.jobs_failed')
                    if player.require_transcription and not stop.is_set():
                        player.fail_transcription(response[1][0])
                        return
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
                jobs.task_done()
    except Exception as exc:
        if not stop.is_set() and not player.stop_flag.is_set():
            LOG.error('whisper_engine_failed type=%s', type(exc).__name__)
            if player.require_transcription:
                player.fail_transcription(type(exc).__name__)
            try:
                events.put_nowait(Event('error', 'Whisper: '+type(exc).__name__))
            except Full:
                pass
    finally:
        parent.close()
        child.close()
        if process.pid is not None:
            pid = process.pid
            if process.is_alive():
                process.terminate()
                process.join(.5)
                if process.is_alive():
                    process.kill()
            process.join()
            LOG.info('whisper_engine_stopped pid=%s exit=%s', pid, process.exitcode)
            process.close()
