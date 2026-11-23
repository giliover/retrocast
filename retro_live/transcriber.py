import datetime as dt
import subprocess
import time
import os
from .performance import MONITOR
import numpy as np
from .events import Event

RATE = 16000


def detect_cpu_threads() -> int:
    """Use Linux nproc (available processing units); fall back if unavailable."""
    try:
        result = subprocess.run(
            ['nproc'], capture_output=True, text=True, check=True, timeout=2
        )
        return max(1, int(result.stdout.strip()))
    except (OSError, ValueError, subprocess.SubprocessError):
        return max(1, os.cpu_count() or 1)



def transcribe(config, processes, events, stop):
    try:
        from faster_whisper import WhisperModel
        events.put(Event('status', 'Carregando modelo Whisper...'))
        model_started=time.perf_counter()
        available_cpus = detect_cpu_threads()
        cpu_threads = max(1, int(os.environ.get('RETROCAST_WHISPER_THREADS', available_cpus)))
        workers = max(1, int(os.environ.get('RETROCAST_WHISPER_WORKERS', max(1, available_cpus // 2))))
        model = WhisperModel(config.model, device=config.device, compute_type=config.compute_type,
                             cpu_threads=cpu_threads, num_workers=workers)
        MONITOR.duration('ai.cpu_threads_configured',cpu_threads)
        MONITOR.duration('ai.workers_configured',workers)
        MONITOR.duration('ai.model_load',(time.perf_counter()-model_started)*1000)
        if stop.is_set():
            return
        events.put(Event('status', 'Conectando à transmissão...'))
        source = processes.start(['streamlink', '--stdout', config.url, config.quality],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        decoder = processes.start(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                                   '-i', 'pipe:0', '-vn', '-ac', '1', '-ar', str(RATE),
                                   '-f', 's16le', 'pipe:1'], stdin=source.stdout,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        source.stdout.close()
        chunk_size = int(config.chunk * RATE * 2)
        count = 0
        while not stop.is_set():
            chunk_started=time.perf_counter()
            buf = bytearray()
            while len(buf) < chunk_size and not stop.is_set():
                part = decoder.stdout.read(min(65536, chunk_size - len(buf)))
                if not part:
                    break
                buf.extend(part)
            if stop.is_set() or len(buf) < RATE * 2:
                break
            MONITOR.duration('ai.audio_wait',(time.perf_counter()-chunk_started)*1000)
            audio_duration_s = len(buf) / (RATE * 2)
            MONITOR.duration('ai.audio_duration', audio_duration_s * 1000)
            inference_started=time.perf_counter()
            audio = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(audio,
                language=None if config.language == 'auto' else config.language,
                beam_size=1, vad_filter=True, condition_on_previous_text=False)
            # Iterating the generator is part of actual inference time.
            segments = list(segments)
            words = ' '.join(s.text.strip() for s in segments).strip()
            inference_ms = (time.perf_counter()-inference_started)*1000
            MONITOR.duration('ai.inference', inference_ms)
            MONITOR.duration('ai.realtime_factor_x1000', inference_ms / max(audio_duration_s, 0.001))
            MONITOR.increment('ai.segments_count', len(segments))
            MONITOR.increment('ai.transcribed_chars', len(words))
            if words:
                MONITOR.increment('ai.chunks_with_text')
            else:
                MONITOR.increment('ai.chunks_without_text')
            # Segment timestamps reflect returned speech, not necessarily exact VAD coverage.
            MONITOR.duration('ai.segment_span', sum(max(0.0, seg.end-seg.start) for seg in segments)*1000)
            MONITOR.increment('ai.chunks_processed')
            count += 1
            if words:
                events.put(Event('line', f'[{dt.datetime.now():%H:%M:%S}] {words}'))
            if stop.is_set():
                break
            events.put(Event('status', f'Transcrevendo • {count} blocos processados'))
            if len(buf) < chunk_size:
                break
        if not stop.is_set():
            events.put(Event('status', 'Áudio encerrado.'))
    except Exception as exc:
        events.put(Event('error', f'Transcrição: {exc}'))
