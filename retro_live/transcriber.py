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


def transcribe(config, player, events, stop):
    try:
        from faster_whisper import WhisperModel
        started = time.monotonic()
        model = WhisperModel(config.model, device=config.device, compute_type=config.compute_type,
                             cpu_threads=max(1, min(4, os.cpu_count() or 1)), num_workers=1)
        MONITOR.duration('ai.model_load', (time.monotonic()-started)*1000)
        LOG.info('whisper_ready')
        while not stop.is_set():
            try:
                start, audio = player.jobs.get(timeout=.2)
            except Empty:
                if player._ended:
                    break
                continue
            began = time.monotonic()
            try:
                segments, _ = model.transcribe(audio, language=None if config.language == 'auto' else config.language,
                                               beam_size=1, vad_filter=False, condition_on_previous_text=False)
                count = 0
                for segment in segments:
                    if stop.is_set():
                        return
                    text = segment.text.strip()[:1000]
                    if text and math.isfinite(segment.start) and math.isfinite(segment.end) and 0 <= segment.start < segment.end <= len(audio)/16000 + .1:
                        try:
                            events.put_nowait(Event('cue', (start+segment.start, start+segment.end, text)))
                            count += 1
                        except Full:
                            MONITOR.increment('ai.cues_dropped')
                elapsed = time.monotonic()-began
                LOG.info('whisper_segment_complete pts=%.2f cues=%d', start, count)
                MONITOR.duration('ai.inference', elapsed*1000)
                MONITOR.duration('ai.realtime_factor_x1000', elapsed/5*1000)
            except Exception as exc:
                LOG.error('whisper_segment_failed type=%s trace=%s', type(exc).__name__, ' > '.join(f'{os.path.basename(f.filename)}:{f.lineno}:{f.name}' for f in traceback.extract_tb(exc.__traceback__)))
    except Exception as exc:
        LOG.error('whisper_start_failed type=%s', type(exc).__name__)
        try:
            events.put_nowait(Event('error', 'Whisper: '+type(exc).__name__))
        except Full:
            pass
