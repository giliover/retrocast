"""PyAV/FFmpeg video decoder + PortAudio audio output, no MPV.
The worker never calls pygame; only the main UI thread creates pygame surfaces.
"""
import collections
import subprocess
import sys
import threading
import time
from .performance import MONITOR, measure
from queue import Queue, Empty

import av
import numpy as np


class VideoPlayer:
    def __init__(self):
        self.frames = Queue(maxsize=2)
        self.stop_flag = threading.Event()
        self.worker = None
        self.error = None
        self.latest = None
        self.paused = False
        self.volume = 0.8
        self.audio = None
        self._audio_lock = threading.Lock()
        self._audio_chunks = collections.deque()
        self._audio_offset = 0
        self._audio_samples = 0
        self._max_audio_samples = 48000 * 3
        self._sample_rate = 48000
        self._clock_start = None
        self._last_video_pts = None
        self._last_video_wall = None
        self.target_video_fps = 30

    def start(self, url, quality='best'):
        self.close()
        self.stop_flag.clear()
        self.error = None
        self.paused = False
        self.frames = Queue(maxsize=2)
        self._clock_start = None
        self._last_video_pts = None
        self._last_video_wall = None
        self.worker = threading.Thread(target=self._run, args=(url, quality), daemon=True)
        self.worker.start()

    def _audio_callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        if self.paused or self.stop_flag.is_set():
            return
        written = 0
        with self._audio_lock:
            while written < frames and self._audio_chunks:
                head = self._audio_chunks[0]
                available = len(head) - self._audio_offset
                take = min(available, frames - written)
                outdata[written:written+take] = head[self._audio_offset:self._audio_offset+take] * self.volume
                written += take
                self._audio_offset += take
                self._audio_samples -= take
                if self._audio_offset >= len(head):
                    self._audio_chunks.popleft()
                    self._audio_offset = 0

    def _enqueue_audio(self, chunk):
        if chunk.size == 0:
            return
        with self._audio_lock:
            # Limit latency and memory when inference or rendering is slow.
            while self._audio_chunks and self._audio_samples + len(chunk) > self._max_audio_samples:
                old = self._audio_chunks.popleft()
                self._audio_samples -= len(old) - self._audio_offset
                self._audio_offset = 0
            self._audio_chunks.append(chunk)
            self._audio_samples += len(chunk)

    def _run(self, url, quality):
        container = None
        try:
            import sounddevice as sd
            resolve_start=time.perf_counter()
            result = subprocess.run([sys.executable, '-m', 'streamlink', '--stream-url', url, quality],
                                    capture_output=True, text=True, timeout=30, check=False)
            MONITOR.duration('video.streamlink_resolve',(time.perf_counter()-resolve_start)*1000)
            if self.stop_flag.is_set():
                return
            if result.returncode:
                raise RuntimeError('Streamlink: ' + (result.stderr.strip()[-500:] or 'Falha ao resolver stream'))
            source = result.stdout.strip().splitlines()[-1]
            if not source:
                raise RuntimeError('Streamlink nao retornou URL de midia')
            open_start=time.perf_counter()
            container = av.open(source, options={'reconnect':'1', 'reconnect_streamed':'1',
                                                  'reconnect_delay_max':'3'}, timeout=(10, 10))
            MONITOR.duration('video.open',(time.perf_counter()-open_start)*1000)
            if self.stop_flag.is_set():
                return
            video = next((s for s in container.streams if s.type == 'video'), None)
            audio = next((s for s in container.streams if s.type == 'audio'), None)
            if video is None:
                raise RuntimeError('A transmissao nao contem video')
            resampler = None
            if audio is not None:
                resampler = av.AudioResampler(format='flt', layout='stereo', rate=self._sample_rate)
                try:
                    self.audio = sd.OutputStream(samplerate=self._sample_rate, channels=2,
                                                 dtype='float32', blocksize=2048,
                                                 callback=self._audio_callback)
                    self.audio.start()
                except Exception as exc:
                    self.audio = None
                    # Video can still run on machines without an audio output device.
                    self.error = 'Audio indisponivel: ' + str(exc)
            for packet in container.demux([s for s in (video, audio) if s is not None]):
                if self.stop_flag.is_set():
                    break
                while self.paused and not self.stop_flag.wait(0.05):
                    pass
                decode_start=time.perf_counter()
                decoded=packet.decode()
                MONITOR.duration('video.packet_decode',(time.perf_counter()-decode_start)*1000)
                for frame in decoded:
                    if self.stop_flag.is_set():
                        break
                    if isinstance(frame, av.VideoFrame):
                        pts = float(frame.time) if frame.time is not None else None
                        if self._clock_start is None:
                            self._clock_start = time.monotonic() - (pts or 0)
                        if pts is not None:
                            deadline = self._clock_start + pts
                            lag = time.monotonic() - deadline
                            if lag > 0.35:
                                MONITOR.increment('video.frames_dropped_late')
                                continue  # Drop stale frames rather than accumulating lag.
                            if lag < -0.01:
                                self.stop_flag.wait(min(-lag, 0.12))
                        # Keep demux/decode running for audio sync, but avoid RGB conversion
                        # for video frames that the 30-FPS UI cannot display.
                        now = time.monotonic()
                        interval = 1.0 / self.target_video_fps
                        if pts is not None:
                            if self._last_video_pts is not None and pts >= self._last_video_pts and pts - self._last_video_pts < interval * 0.95:
                                MONITOR.increment('video.frames_skipped_before_rgb')
                                continue
                            self._last_video_pts = pts
                        else:
                            if self._last_video_wall is not None and now - self._last_video_wall < interval * 0.95:
                                MONITOR.increment('video.frames_skipped_before_rgb')
                                continue
                            self._last_video_wall = now
                        convert_start=time.perf_counter()
                        rgb = frame.to_ndarray(format='rgb24')
                        MONITOR.duration('video.rgb_conversion',(time.perf_counter()-convert_start)*1000)
                        item = (rgb.tobytes(), (frame.width, frame.height))
                        MONITOR.increment('video.frames_rgb_converted')
                        if self.frames.full():
                            MONITOR.increment('video.frames_dropped_queue')
                            try: self.frames.get_nowait()
                            except Empty: pass
                        self.frames.put_nowait(item)
                    elif isinstance(frame, av.AudioFrame) and resampler and self.audio:
                        for converted in resampler.resample(frame):
                            samples = converted.to_ndarray()
                            # planar stereo (2, N) or packed (1, 2*N)
                            if samples.ndim == 2 and samples.shape[0] == 2:
                                samples = samples.T
                            else:
                                samples = samples.reshape(-1, 2)
                            self._enqueue_audio(np.ascontiguousarray(samples, dtype=np.float32))
                            MONITOR.increment('audio.chunks_queued')
            if not self.stop_flag.is_set() and self.error is None:
                self.error = 'Transmissao encerrada'
        except Exception as exc:
            self.error = str(exc)
        finally:
            if container is not None:
                container.close()
            if self.audio is not None:
                try: self.audio.stop(); self.audio.close()
                except Exception: pass
                self.audio = None

    def poll(self):
        item = None
        while True:
            try:
                newer = self.frames.get_nowait()
                if item is not None:
                    MONITOR.increment('video.frames_skipped_ui_poll')
                item = newer
            except Empty: break
        return item

    def toggle_pause(self):
        self.paused = not self.paused
        # Resume on a fresh clock: avoid dropping every frame after a pause.
        if not self.paused:
            self._clock_start = None
        self._last_video_pts = None
        self._last_video_wall = None

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, float(volume)))

    def close(self):
        self.stop_flag.set()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=3.0)
        stopped = not (self.worker and self.worker.is_alive())
        if stopped:
            self.worker = None
        with self._audio_lock:
            self._audio_chunks.clear()
            self._audio_offset = 0
            self._audio_samples = 0
        self.frames = Queue(maxsize=2)
        self.latest = None
        self._clock_start = None
        return stopped
