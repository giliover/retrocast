import unittest
import numpy as np
from retro_live.player import VideoPlayer, BLOCK, RATE
from retro_live.session import Session
from retro_live.events import Event

class WhisperWaitTests(unittest.TestCase):
    def setup_player(self):
        p = VideoPlayer()
        p.set_priority("subtitle")
        p.set_delay(40)
        p.latest = p.video_latest = 40
        p.sound[0] = np.ones((BLOCK, 2), dtype=np.float32)
        return p, np.zeros((960, 2), dtype=np.float32)

    def test_wait_and_resume_exact_sample(self):
        p, out = self.setup_player()
        p._callback(out, 960, None, None)
        self.assertTrue(p.whisper_waiting)
        self.assertEqual(p._play_sample, 0)
        self.assertFalse(out.any())
        p.acknowledge_transcription(0, .1)
        p._callback(out, 960, None, None)
        self.assertFalse(p.whisper_waiting)
        self.assertEqual(p._play_sample, 960)
        self.assertTrue(np.allclose(out, .8))

    def test_later_completion_does_not_hide_gap(self):
        p, out = self.setup_player()
        p.sound[1] = p.sound[0]
        p.acknowledge_transcription(.1, .2)
        p._callback(out, 960, None, None)
        self.assertTrue(p.whisper_waiting)
        self.assertEqual(p._play_sample, 0)

    def test_silent_completion_and_ui_ack(self):
        s = Session()
        s.video, out = self.setup_player()
        s.running = True
        s.video._callback(out, 960, None, None)
        s.events.put_nowait(Event('transcription_complete', (0., .1)))
        with self.assertLogs('retrocast.application', 'INFO') as logs:
            s.poll()
            self.assertEqual(s.status, 'WAITING FOR WHISPER...')
            s.video._callback(out, 960, None, None)
            s.poll()
        self.assertIn('whisper_wait_started', '\n'.join(logs.output))
        self.assertIn('whisper_wait_ended', '\n'.join(logs.output))
        self.assertEqual(s.caption, '')
        self.assertEqual(s.video._play_sample, 960)

    def test_cross_block_wait(self):
        p, out = self.setup_player()
        p.sound[1] = p.sound[0]
        p.acknowledge_transcription(0, .1)
        p._play_sample = BLOCK - 480
        p._callback(out, 960, None, None)
        self.assertEqual(p._play_sample, BLOCK - 480)
        self.assertFalse(out.any())
        p.acknowledge_transcription(.1, .2)
        p._callback(out, 960, None, None)
        self.assertEqual(p._play_sample, BLOCK + 480)

    def test_manual_pause_stays_paused(self):
        p, out = self.setup_player()
        p.acknowledge_transcription(0, .1)
        p.toggle_pause()
        p._callback(out, 960, None, None)
        self.assertFalse(out.any())
        self.assertIsNone(p._play_sample)
