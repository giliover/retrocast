"""Consume timestamped PCM from the same capture as playback."""
import logging
import os
import time
import traceback
import math
from queue import Empty, Full
from .events import Event
from .performance import MONITOR

LOG = logging.getLogger('retrocast.application')


def publish(events, event, stop, player):
    while not stop.is_set() and not player.stop_flag.is_set():
        try:
            events.put(event, timeout=.2)
            return True
        except Full:
            continue
    return False


def transcribe(config, player, events, stop):
    try:
        from faster_whisper import WhisperModel
        started = time.monotonic()
        model = WhisperModel(config.model, device=config.device, compute_type=config.compute_type,
                             cpu_threads=max(1, min(4, os.cpu_count() or 1)), num_workers=1)
        MONITOR.duration('ai.model_load', (time.monotonic()-started)*1000)
        LOG.info('whisper_ready')
        while not stop.is_set() and not player.stop_flag.is_set():
            try:
                start, audio = player.jobs.get(timeout=.2)
            except Empty:
                if player._ended:
                    break
                continue
            began = time.monotonic()
            duration = len(audio)/16000
            player.ai_active = start
            MONITOR.increment("ai.jobs_started")
            try:
                segments, _ = model.transcribe(audio, language=None if config.language == 'auto' else config.language,
                                               beam_size=1, vad_filter=False, condition_on_previous_text=False)
                count = rejected = dropped = 0
                for segment in segments:
                    if stop.is_set():
                        return
                    text = segment.text.strip()[:1000]
                    if text and math.isfinite(segment.start) and math.isfinite(segment.end) and 0 <= segment.start < segment.end <= len(audio)/16000 + .1:
                        if not publish(events, Event('cue', (start+segment.start, start+segment.end, text)), stop, player):
                            return
                        count += 1
                    else:
                        rejected += 1
                elapsed = time.monotonic()-began
                if not publish(events, Event("transcription_complete", (start, start + duration)), stop, player):
                    return
                player.ai_last_completed = start + duration
                pos = player.position
                LOG.info('whisper_segment_complete pts=%.2f end=%.2f cues=%d rejected=%d dropped=%d elapsed=%.3f rtf=%.3f queue=%d playback=%s lead=%s', start, start+duration, count, rejected, dropped, elapsed, elapsed/max(duration,.001), player.jobs.qsize(), pos, None if pos is None else round(start+duration-pos,3))
                MONITOR.increment('ai.jobs_completed')
                MONITOR.increment('ai.cues_emitted', count)
                MONITOR.increment('ai.cues_rejected', rejected)
                MONITOR.duration('ai.inference', elapsed*1000)
                MONITOR.duration('ai.realtime_factor_x1000', elapsed/max(duration,.001)*1000)
            except Exception as exc:
                MONITOR.increment('ai.jobs_failed')
                LOG.error('whisper_segment_failed pts=%.2f type=%s trace=%s', start, type(exc).__name__, ' > '.join(f'{os.path.basename(f.filename)}:{f.lineno}:{f.name}' for f in traceback.extract_tb(exc.__traceback__)))
                if player.require_transcription:
                    player.fail_transcription(type(exc).__name__)
                    return
            finally:
                player.ai_active = None
                player.jobs.task_done()
    except Exception as exc:
        LOG.error('whisper_start_failed type=%s', type(exc).__name__)
        if player.require_transcription:
            player.fail_transcription(type(exc).__name__)
        try:
            events.put_nowait(Event('error', 'Whisper: '+type(exc).__name__))
        except Full:
            pass
