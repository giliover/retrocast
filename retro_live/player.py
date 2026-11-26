"""Single capture, bounded timestamped audio/video buffers and shared playback clock."""
import logging
import threading
import time
import traceback
from .capture import StreamCapture
from .playback_policy import DEFAULT_DELAY, PRIORITIES, FPS_CHOICES, LatestAudioQueue, WaitPolicy, effective_fps
from .whisper_policy import WhisperPolicy
from collections import deque
from .packet_buffer import PacketBuffer
from .video_decoder import decode_video
import numpy as np
from .performance import MONITOR

LOG = logging.getLogger('retrocast.application')
RATE = 48000
BLOCK = 4800


class VideoPlayer:
    def __init__(self):
        self.stop_flag = threading.Event()
        self.worker = None
        self.capture = StreamCapture()
        self.error = None
        self.paused = False
        self.volume = .8
        self.delay = DEFAULT_DELAY
        self.audio = None
        self.lock = threading.Lock()
        self.frames = deque(maxlen=12)
        self.packets = PacketBuffer()
        self._video_generation = 0
        self._video_target = None
        self._video_ready = -1.0
        self._decoder = None
        self._capture_done = False
        self.fps = 30.0
        self.fps_limit = 0
        self.priority = "video"
        self._wait_policy = WaitPolicy()
        self.ai_bypassed_callbacks = 0
        self._skipped_blocks = set()
        self.sound = {}
        self.jobs = LatestAudioQueue(maxsize=8)
        self.latest = -1.0
        self.position = None
        self._last_frame = None
        self.presented_video_pts = None
        self._wall = None
        self._play_sample = None
        self._origin = None
        self._audio_next = 0
        self._pending = np.empty((0, 2), dtype=np.float32)
        self._pcm = []
        self._pcm_start = 0
        self._last_video = -1
        self._last_audio = -1
        self.video_latest = -1.0
        self._ended = False
        self._resume_edge = None
        self.ai_last_enqueued = None
        self.ai_last_completed = None
        self.ai_active = None
        self.whisper_policy = WhisperPolicy()
        self.ai_attempt = 0
        self.ai_policy = None
        self.ai_expired = 0
        self.ai_dropped = 0
        self.require_transcription = False
        self.subtitles_enabled = True
        self._ai_cutoff = 0
        self._ai_lock = threading.Lock()
        self.whisper_waiting = False
        self._transcribed_blocks = set()
        self.audio_discontinuities = 0

    def start(self, url, quality='auto', delay=DEFAULT_DELAY, require_transcription=None, priority=None, fps_limit=0, subtitles_enabled=True, whisper_policy=None):
        if not self.close():
            raise RuntimeError('Previous player still stopping')
        self.__init__()
        self.delay = delay
        self.whisper_policy = whisper_policy or WhisperPolicy()
        self.set_priority(priority or ("balanced" if require_transcription is None else ("subtitle" if require_transcription else "video")))
        self.set_fps_limit(fps_limit)
        self.set_subtitles(subtitles_enabled)
        self.worker = threading.Thread(target=self._run, args=(url, quality), daemon=True)
        self.worker.start()

    @property
    def presentation_fps(self):
        return effective_fps(self.fps, self.fps_limit)

    def set_priority(self, priority):
        if priority not in PRIORITIES:
            raise ValueError('Invalid playback priority')
        with self.lock:
            self.priority = priority
            self.require_transcription = self.subtitles_enabled and priority == 'subtitle'
            self._wait_policy.reset()
            self.whisper_waiting = False
        LOG.info('playback_priority mode=%s', priority)

    def set_subtitles(self, enabled):
        with self._ai_lock:
            with self.lock:
                if self.subtitles_enabled == enabled:
                    return
                self.subtitles_enabled = enabled
                self.require_transcription = enabled and self.priority == 'subtitle'
                self.whisper_waiting = False
                self._wait_policy.reset()
                self._ai_cutoff = max(0, round(self.latest * RATE / BLOCK))
                self._transcribed_blocks.clear()
                self._skipped_blocks.clear()
                self._pcm.clear()
                self.jobs = LatestAudioQueue(maxsize=8)
                self.ai_last_enqueued = self.ai_last_completed = None
        LOG.info('whisper_capture_enabled=%s cutoff_block=%d', enabled, self._ai_cutoff)

    def set_fps_limit(self, limit):
        if type(limit) is not int or limit not in FPS_CHOICES:
            raise ValueError('Invalid FPS limit')
        with self.lock:
            self.fps_limit = limit
        LOG.info('video_fps_limit limit=%s effective=%.2f', limit or 'auto', self.presentation_fps)

    def set_whisper_policy(self, policy):
        if not isinstance(policy, WhisperPolicy):
            raise ValueError("Invalid Whisper policy")
        self.whisper_policy = policy
        LOG.info("whisper_policy retries=%d wait_timeout=%.1f", policy.retries, policy.timeout)

    def discard_transcription(self, start, end):
        first = round(start * RATE / BLOCK)
        last = round(end * RATE / BLOCK)
        if not 0 <= last - first <= 50:
            raise ValueError("Invalid transcription interval")
        with self.lock:
            for index in range(first, last):
                if index in self.sound:
                    self._skipped_blocks.add(index)

    def _enqueue_audio(self, job):
        full, dropped = self.jobs.offer(job)
        self.ai_last_enqueued = job[0] + len(job[1])/16000
        MONITOR.increment('ai.jobs_enqueued')
        if full:
            self.ai_dropped += 1
            if dropped is not None:
                start, audio = dropped
                first = round(start * RATE / BLOCK)
                last = first + round(len(audio) / 1600)
                with self.lock:
                    for index in range(first, last):
                        if index in self.sound:
                            self._skipped_blocks.add(index)
                LOG.warning('ai_queue_full policy=drop_oldest dropped_pts=%.2f newest_pts=%.2f dropped_total=%d depth=%d', start, job[0], self.ai_dropped, self.jobs.qsize())
            else:
                LOG.warning('ai_queue_full policy=drop_oldest dropped_total=%d', self.ai_dropped)
            MONITOR.increment('ai.jobs_dropped')

    def set_delay(self, seconds):
        with self.lock:
            self.delay = max(10, min(120, int(seconds)))
            self.position = None
            self._last_frame = None
            self._play_sample = None
            self._wall = None
            self._resume_edge = None
            self.whisper_waiting = False
            self._wait_policy.reset()
            self._reset_video()

    def _reset_video(self):
        self.presented_video_pts = None
        self._video_generation += 1
        self._video_ready = -1.0
        self._video_target = None
        self.frames.clear()

    def _time(self, frame):
        if frame.time is None:
            return None
        pts = float(frame.time)
        if self._origin is None:
            self._origin = pts
        return max(0.0, pts - self._origin)

    def acknowledge_transcription(self, start, end):
        """Called only after the UI has consumed all cues for this audio job."""
        first = round(start * RATE / BLOCK)
        last = round(end * RATE / BLOCK)
        if not 0 <= last - first <= 50:
            raise ValueError('Invalid transcription interval')
        with self.lock:
            for index in range(first, last):
                if index in self.sound:
                    self._transcribed_blocks.add(index)

    def fail_transcription(self, reason):
        self.error = 'Whisper: ' + reason
        self.stop_flag.set()
        self.capture.terminate()

    def _transcription_ready(self, sample, count):
        if count <= 0:
            return True
        first = sample // BLOCK
        last = (sample + count - 1) // BLOCK
        return all(i < self._ai_cutoff or i in self._transcribed_blocks or i in self._skipped_blocks for i in range(first, last + 1))

    def _callback(self, outdata, frames, time_info, status):
        outdata.fill(0)
        if self.stop_flag.is_set():
            return
        with self.lock:
            if self.paused:
                self.whisper_waiting = False
                return
            edge = min(self.latest, self.video_latest)
            if self._play_sample is None:
                if self._resume_edge is not None and edge < self._resume_edge and not self._ended:
                    return
                self._resume_edge = None
                if edge < 0 or (edge < self.delay and not self._ended):
                    return
                target = max(0., edge-self.delay)
                if self._decoder is not None:
                    if not self.packets.keys:
                        return
                    target = max(target, self.packets.keys[0][1], (next(iter(self.sound), 0)*BLOCK)/RATE)
                    if target > edge:
                        return
                    if self._video_target is None:
                        self._video_target = target
                    target = self._video_target
                    if self._video_ready < target:
                        return
                self._play_sample = int(target*RATE)
            if edge - self._play_sample/RATE > (129 if self.require_transcription else 125):
                if self.require_transcription and edge - self._play_sample/RATE > 129:
                    self.error = 'Playback buffer exhausted while waiting for Whisper'
                    self.stop_flag.set()
                    return
                self._play_sample = None
                self.position = None
                self._reset_video()
                self._last_frame = None
                return
            if not self._ended and self._play_sample + frames > int(edge*RATE):
                # In strict mode keep the exact cursor rather than seeking.
                if self.require_transcription:
                    return
                # Refill instead of advancing across an unavailable interval.
                self._play_sample = None
                self.position = None
                self._resume_edge = edge + self.delay
                self._reset_video()
                MONITOR.increment('audio.rebuffer')
                return
            sample = self._play_sample
            if self._decoder is not None:
                self._video_target = sample / RATE
                if self._video_ready + .10 < self._video_target and not self._ended:
                    return
            if self._ended and sample >= int(edge*RATE):
                self.position = edge
                self.whisper_waiting = False
                return
            limit = min(frames, max(0, int(edge*RATE)-sample)) if self._ended else frames
            mode = self.priority if self.subtitles_enabled else 'video'
            ready = not self.subtitles_enabled or self._transcription_ready(sample, limit)
            if not self._wait_policy.allows(mode, ready, time.monotonic()):
                self.whisper_waiting = True
                self.position = sample / RATE
                return
            if not ready or sample // BLOCK in self._skipped_blocks:
                self.ai_bypassed_callbacks += 1
            self.whisper_waiting = False
            self.position = sample / RATE
            written = 0
            while written < limit:
                index, offset = divmod(sample, BLOCK)
                take = min(limit - written, BLOCK - offset)
                data = self.sound.get(index)
                if data is not None:
                    outdata[written:written+take] = data[offset:offset+take] * self.volume
                sample += take
                written += take
            self._play_sample = sample

    def _store_audio(self, samples, pts):
        # The stereo playback blocks and mono inference blocks share the same timeline.
        expected = self._audio_next + len(self._pending)
        actual = int(round(pts * RATE))
        if abs(actual - expected) > RATE // 2:
            self.audio_discontinuities += 1
            if self.require_transcription:
                self.fail_transcription("audio timestamp discontinuity")
                return
            LOG.warning("audio_pts_discontinuity expected=%.3f actual=%.3f discarded_blocks=%d", expected/RATE, actual/RATE, len(self._pcm))
            self._pending = np.empty((0, 2), dtype=np.float32)
            with self._ai_lock:
                self._pcm.clear()
            self._audio_next = max(0, actual // BLOCK * BLOCK)
        self._pending = np.concatenate((self._pending, samples))
        while len(self._pending) >= BLOCK:
            block = self._pending[:BLOCK].copy()
            self._pending = self._pending[BLOCK:]
            index = self._audio_next // BLOCK
            with self.lock:
                self.sound[index] = block
                self.sound.pop(index - 1300, None)
                self._transcribed_blocks.discard(index - 1300)
                self._skipped_blocks.discard(index - 1300)
                # Bound storage even after timestamp discontinuities.
                if len(self.sound) > 1300:
                    oldest = next(iter(self.sound))
                    self.sound.pop(oldest)
                    self._transcribed_blocks.discard(oldest)
                    self._skipped_blocks.discard(oldest)
                self.latest = max(self.latest, (index + 1) * .1)
            with self._ai_lock:
                if self.subtitles_enabled and index >= self._ai_cutoff:
                    if not self._pcm:
                        self._pcm_start = index * .1
                    self._pcm.append(block.reshape(-1, 3, 2).mean(axis=(1, 2), dtype=np.float32))
                    if len(self._pcm) == 50:
                        job = (self._pcm_start, np.concatenate(self._pcm))
                        self._pcm.clear()
                        self._enqueue_audio(job)
            self._audio_next += BLOCK

    def _run(self, url, quality):
        container = None
        stage = 'dependencies'
        try:
            import av
            import sounddevice as sd
            stage = 'streamlink_start'
            source = self.capture.start(url, quality, self.stop_flag)
            if source is None:
                return
            stage = 'pyav_open'
            container = av.open(source, mode='r')
            stage = 'stream_selection'
            video = next(iter(container.streams.video), None)
            audio = next(iter(container.streams.audio), None)
            if video is None or audio is None:
                raise RuntimeError('Audio/video stream required')
            resampler = av.AudioResampler(format='fltp', layout='stereo', rate=RATE)
            stage = "audio_output"
            self.audio = sd.OutputStream(samplerate=RATE, channels=2, dtype='float32', blocksize=960, callback=self._callback)
            LOG.info('capture_started delay=%d', self.delay)
            stage = "demux_decode"
            self.fps = min(120., max(1., float(video.average_rate or 30)))
            self._decoder = threading.Thread(target=decode_video, args=(self,video), daemon=True)
            self._decoder.start()
            self.audio.start()
            LOG.info("video_source width=%s height=%s fps=%.3f quality=%s", video.codec_context.width, video.codec_context.height, self.fps, quality)
            for packet in container.demux(video, audio):
                if self.stop_flag.is_set():
                    break
                # Bound the lead while Whisper is slow. Do not discard unplayed media.
                while self.require_transcription and not self.stop_flag.is_set():
                    with self.lock:
                        cursor = self._play_sample / RATE if self._play_sample is not None else (self._video_target or 0.)
                        ahead = max(self.latest, self.video_latest) - cursor
                    if ahead < max(110, self.delay + 5):
                        break
                    self.stop_flag.wait(.05)
                if self.stop_flag.is_set():
                    break
                if packet.stream.index == video.index:
                    if packet.pts is None or not packet.size:
                        continue
                    stamp = float(packet.pts * packet.time_base)
                    if self._origin is None:
                        self._origin = stamp
                    pts = max(0., stamp-self._origin)
                    with self.lock:
                        if self.packets.append(packet, pts):
                            self.video_latest = self.packets.edge
                            MONITOR.increment('video.compressed_bytes', packet.size)
                    continue
                for frame in packet.decode():
                    pts = self._time(frame)
                    if pts is None:
                        continue
                    for converted in resampler.resample(frame):
                        t = self._time(converted)
                        self._store_audio(converted.to_ndarray().T, pts if t is None else t)
            with self._ai_lock:
                if self.subtitles_enabled and self._pcm and not self.stop_flag.is_set():
                    job = (self._pcm_start, np.concatenate(self._pcm))
                    self._pcm.clear()
                    self._enqueue_audio(job)
            self._capture_done = True
            code = self.capture.returncode()
            if code not in (None, 0) and not self.stop_flag.is_set():
                raise RuntimeError("Streamlink exited unsuccessfully")
            self._ended = True
            while not self.stop_flag.wait(.1):
                if min(self.latest, self.video_latest) < 0 or (self.position is not None and self.position >= min(self.latest,self.video_latest)):
                    break
        except Exception as exc:
            if not self.stop_flag.is_set():
                self.error = f'Capture failed: {stage} ({type(exc).__name__})'
                trace = ' > '.join(f'{f.filename.rsplit("/", 1)[-1]}:{f.lineno}:{f.name}' for f in traceback.extract_tb(exc.__traceback__))
                LOG.error('capture_failed stage=%s type=%s errno=%s streamlink_exit=%s trace=%s', stage, type(exc).__name__, getattr(exc, 'errno', None), self.capture.returncode(), trace)
        finally:
            self._ended = True
            self.stop_flag.set()
            self.capture.terminate()
            if self._decoder is not None:
                self._decoder.join()
            try:
                if container is not None:
                    container.close()
            finally:
                self.capture.close()
                if self.audio is not None:
                    try:
                        self.audio.stop()
                    finally:
                        self.audio.close()
                        self.audio = None
                LOG.info("capture_ended")

    def poll(self):
        with self.lock:
            if self.position is None:
                return None
            item = None
            for _ in range(12):
                if not self.frames or self.frames[0][0] > self.position + .015:
                    break
                self.presented_video_pts, item = self.frames.popleft()
            return item

    def toggle_pause(self):
        with self.lock:
            self.paused = not self.paused
            self._wait_policy.reset()
            self._wall = time.monotonic()

    def set_volume(self, volume):
        self.volume = max(0., min(1., float(volume)))

    def close(self):
        self.stop_flag.set()
        self.capture.terminate()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=.1)
        return not (self.worker and self.worker.is_alive())
