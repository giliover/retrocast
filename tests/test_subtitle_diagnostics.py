import unittest
from unittest.mock import patch
import numpy as np
from retro_live.session import Session
from retro_live.events import Event
from retro_live.player import VideoPlayer, BLOCK

class SubtitleDiagnosticsTests(unittest.TestCase):
    def test_late_cue_and_periodic_snapshot(self):
        s = Session()
        s.running = True
        s.video.position = 20
        s.events.put_nowait(Event('cue', (1., 2., 'private text')))
        s._diag_at = -100
        with self.assertLogs('retrocast.application', 'INFO') as logs:
            s.poll()
        line = '\n'.join(logs.output)
        self.assertIn('late_total=1', line)
        self.assertIn('subtitle_sync', line)
        self.assertNotIn('private text', line)
        self.assertEqual(s.caption, '')

    def test_queue_overflow_counter(self):
        p = VideoPlayer()
        for _ in range(p.jobs.maxsize):
            p.jobs.put_nowait(None)
        with self.assertLogs('retrocast.application', 'WARNING') as logs:
            for i in range(50):
                p._store_audio(np.zeros((BLOCK, 2), dtype=np.float32), i*.1)
        self.assertEqual(p.ai_dropped, 1)
        self.assertIn('ai_queue_full', '\n'.join(logs.output))

    def test_discontinuity_counter(self):
        p = VideoPlayer()
        with self.assertLogs('retrocast.application', 'WARNING'):
            p._store_audio(np.zeros((BLOCK, 2), dtype=np.float32), 5.)
        self.assertEqual(p.audio_discontinuities, 1)
