import unittest
from unittest.mock import patch
import numpy as np
from retro_live.config import Config
from retro_live.playback_policy import LatestAudioQueue, FrameLimiter, WaitPolicy, effective_fps
from retro_live.player import VideoPlayer, BLOCK


class PolicyTests(unittest.TestCase):
    def test_defaults(self):
        c = Config()
        self.assertEqual((c.delay, c.priority, c.fps_limit, c.language), (15, 'balanced', 0, 'auto'))

    def test_atomic_drop_oldest(self):
        q = LatestAudioQueue(2)
        self.assertEqual(q.offer(1), (False, None))
        q.offer(2)
        self.assertEqual(q.offer(3), (True, 1))
        self.assertEqual([q.get_nowait(), q.get_nowait()], [2, 3])
        q.task_done(); q.task_done()
        self.assertEqual(q.unfinished_tasks, 0)

    def player(self, priority):
        p = VideoPlayer(); p.set_priority(priority)
        p.latest = p.video_latest = 15
        p.sound[0] = np.ones((BLOCK, 2), dtype=np.float32)
        return p, np.zeros((960, 2), dtype=np.float32)

    def test_video_does_not_wait(self):
        p, out = self.player('video')
        p._callback(out, 960, None, None)
        self.assertFalse(p.whisper_waiting)
        self.assertTrue(out.any())

    def test_balanced_timeout_and_reset(self):
        p, out = self.player('balanced')
        with patch('retro_live.player.time.monotonic', return_value=10):
            p._callback(out, 960, None, None)
        self.assertTrue(p.whisper_waiting)
        with patch('retro_live.player.time.monotonic', return_value=12):
            p._callback(out, 960, None, None)
        self.assertFalse(p.whisper_waiting)
        self.assertEqual(p._play_sample, 960)
        p.acknowledge_transcription(0, .1)
        p._callback(out, 960, None, None)
        self.assertIsNone(p._wait_policy.since)

    def test_strict_overflow_releases_only_discarded(self):
        p, out = self.player('subtitle')
        p.jobs = LatestAudioQueue(1)
        pcm = np.zeros(1600, dtype=np.float32)
        p._enqueue_audio((0., pcm))
        with self.assertLogs('retrocast.application', 'WARNING'):
            p._enqueue_audio((.1, pcm))
        self.assertEqual(p.jobs.get_nowait()[0], .1)
        self.assertEqual(p.ai_dropped, 1)
        self.assertTrue(p._transcription_ready(0, 960))
        self.assertFalse(p._transcription_ready(BLOCK, 960))
        p._callback(out, 960, None, None)
        self.assertTrue(out.any())

    def test_switch_priority_while_waiting(self):
        p, out = self.player('subtitle')
        p._callback(out, 960, None, None)
        self.assertTrue(p.whisper_waiting)
        p.set_priority('video')
        p._callback(out, 960, None, None)
        self.assertTrue(out.any())

    def test_fps_selection(self):
        limiter = FrameLimiter()
        selected = sum(limiter.allows(i/60, 15) for i in range(600))
        self.assertEqual(selected, 150)
        self.assertTrue(limiter.allows(10, 30))
        self.assertTrue(limiter.allows(10.01, 0))
        self.assertEqual(effective_fps(24,60),24)
        p = VideoPlayer()
        p.set_fps_limit(15)
        self.assertEqual(p.presentation_fps,15)
        with self.assertRaises(ValueError): p.set_fps_limit(1000)
        with self.assertRaises(ValueError): p.set_priority('invalid')
