"""Decode compressed packets just ahead of the shared audio clock."""
import logging
import time
from .performance import MONITOR

LOG = logging.getLogger('retrocast.application')


def decode_video(player, stream):
    generation = -1
    cursor = None
    context = stream.codec_context
    try:
        while not player.stop_flag.is_set():
            with player.lock:
                target = player._video_target
                current = player._video_generation
                if current != generation:
                    cursor = None
                    generation = current
                    context_reset = True
                else:
                    context_reset = False
                if target is not None and cursor is None:
                    cursor = player.packets.seek(target)
                    context_reset = True
                entry = None
                if cursor is not None and cursor < player.packets.first:
                    cursor = None
                    player._play_sample = None
                    player.position = None
                    player._reset_video()
                if cursor is not None and target is not None and player._video_ready < target + .08:
                    entry = player.packets.get(cursor)
                    if entry is not None:
                        cursor += 1
                eof = player._capture_done and cursor is not None and cursor >= player.packets.next
            if context_reset:
                context.flush_buffers()
            if entry is None and not eof:
                player.stop_flag.wait(.005)
                continue
            started = time.perf_counter()
            frames = context.decode(entry.packet if entry is not None else None)
            for frame in frames:
                if frame.time is None:
                    continue
                pts = max(0., float(frame.time)-player._origin)
                with player.lock:
                    if generation != player._video_generation:
                        break
                    target = player._video_target
                # Decode reference frames, but do not convert obsolete pictures to RGB.
                if target is None or pts < target-.10:
                    continue
                if frame.width*frame.height > 4096*2160:
                    raise ValueError('Video resolution exceeds safety limit')
                rgb = frame.to_ndarray(format='rgb24')
                item = (rgb.tobytes(), (frame.width, frame.height))
                with player.lock:
                    if generation == player._video_generation:
                        player.frames.append((pts, item))
                        player._video_ready = max(player._video_ready, pts)
                MONITOR.increment('video.frames_decoded')
            MONITOR.duration('video.decode', (time.perf_counter()-started)*1000)
            if eof:
                with player.lock:
                    if generation == player._video_generation:
                        player._video_ready = max(player._video_ready, player.video_latest)
                # Remain available for seeks until playback ends.
                while not player.stop_flag.wait(.02):
                    with player.lock:
                        if generation != player._video_generation:
                            break
    except Exception as exc:
        LOG.error('video_decode_failed type=%s', type(exc).__name__)
        player.error = 'Video decoder: '+type(exc).__name__
        player.stop_flag.set()
        player.capture.terminate()
