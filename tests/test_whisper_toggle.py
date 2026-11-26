import unittest
import time
import tempfile
import sys
from pathlib import Path
from threading import Event, Thread
from queue import Queue
import numpy as np
from retro_live.player import VideoPlayer, BLOCK
from retro_live.session import Session
from retro_live.transcriber import transcribe
from retro_live.config import Config
from retro_live.events import Event as SubtitleEvent


class WhisperToggleTests(unittest.TestCase):
    def test_off_resumes_strict_playback_and_drops_jobs(self):
        p = VideoPlayer()
        p.set_priority('subtitle')
        p.latest = p.video_latest = 15
        p.sound[0] = np.ones((BLOCK, 2), dtype=np.float32)
        out = np.zeros((960, 2), dtype=np.float32)
        p._callback(out, 960, None, None)
        self.assertTrue(p.whisper_waiting)
        p.jobs.offer((0., np.zeros(80000)))
        p.set_subtitles(False)
        self.assertEqual(p.jobs.qsize(), 0)
        self.assertFalse(p.require_transcription)
        p._callback(out, 960, None, None)
        self.assertTrue(out.any())
        self.assertFalse(p.whisper_waiting)
        p.set_priority('subtitle')
        self.assertFalse(p.require_transcription)

    def test_off_does_not_generate_pcm_and_on_skips_old_audio(self):
        p = VideoPlayer()
        p.set_subtitles(False)
        for i in range(50):
            p._store_audio(np.zeros((BLOCK, 2), dtype=np.float32), i*.1)
        self.assertFalse(p._pcm)
        self.assertEqual(p.jobs.qsize(), 0)
        p.set_subtitles(True)
        self.assertTrue(p._transcription_ready(0, BLOCK))
        self.assertFalse(p._transcription_ready(50*BLOCK, BLOCK))
        for i in range(50, 100):
            p._store_audio(np.zeros((BLOCK, 2), dtype=np.float32), i*.1)
        self.assertEqual(p.jobs.get_nowait()[0], 5.)

    def test_old_events_isolated(self):
        s = Session()
        old = s.events
        s.set_subtitles(False)
        old.put(SubtitleEvent('cue', (0., 1., 'obsolete')))
        s.poll()
        self.assertFalse(s.cues)
        self.assertEqual(s.caption, '')

    def test_cancel_native_inference_in_separate_process(self):
        # Spawn imports a fake engine that blocks in transcribe, as native code may.
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'inference_started'
            Path(directory, 'faster_whisper.py').write_text(
                'import time\nfrom pathlib import Path\nclass WhisperModel:\n'
                ' def __init__(self, *a, **kw): pass\n'
                f' def transcribe(self, *a, **kw):\n  Path({str(marker)!r}).touch()\n  time.sleep(60)\n')
            sys.path.insert(0, directory)
            p = VideoPlayer()
            p.jobs.offer((0., np.zeros(80000, dtype=np.float32)))
            stop = Event()
            t = Thread(target=transcribe, args=(Config(), p, Queue(), stop), daemon=True)
            try:
                t.start()
                deadline = time.monotonic()+10
                while not marker.exists() and t.is_alive() and time.monotonic()<deadline:
                    time.sleep(.05)
                self.assertTrue(marker.exists())
                stop.set()
                t.join(3)
                self.assertFalse(t.is_alive())
                self.assertIsNone(p.ai_active)
            finally:
                stop.set()
                t.join(3)
                sys.path.remove(directory)
