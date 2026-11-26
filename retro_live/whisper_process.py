"""Isolate native inference so OFF can cancel even a running CTranslate2 call."""
import os
import math
import time
import traceback


def _trace(exc):
    return ' > '.join(f'{os.path.basename(f.filename)}:{f.lineno}:{f.name}'
                      for f in traceback.extract_tb(exc.__traceback__))


def run_engine(connection, config):
    try:
        from faster_whisper import WhisperModel
        began = time.monotonic()
        model = WhisperModel(config.model, device=config.device,
                             compute_type=config.compute_type,
                             cpu_threads=max(1, min(4, os.cpu_count() or 1)), num_workers=1)
        connection.send(('ready', time.monotonic()-began))
        while True:
            start, audio = connection.recv()
            try:
                segments, _ = model.transcribe(audio, language=None if config.language == 'auto' else config.language,
                                               beam_size=1, vad_filter=False, condition_on_previous_text=False)
                cues = []
                rejected = 0
                duration = len(audio)/16000
                for segment in segments:
                    text = segment.text.strip()[:1000]
                    if (text and math.isfinite(segment.start) and math.isfinite(segment.end)
                            and 0 <= segment.start < segment.end <= duration + .1 and len(cues) < 256):
                        cues.append((start+segment.start, start+segment.end, text))
                    else:
                        rejected += 1
                connection.send(('result', (cues, rejected)))
            except Exception as exc:
                connection.send(('failed', (type(exc).__name__, _trace(exc))))
    except (EOFError, BrokenPipeError):
        pass
    except Exception as exc:
        try:
            connection.send(('failed', (type(exc).__name__, _trace(exc))))
        except (EOFError, OSError):
            pass
    finally:
        connection.close()
