import unittest
from unittest.mock import patch
from queue import Queue
from threading import Event
import numpy as np
from retro_live.config import Config
from retro_live.player import VideoPlayer, BLOCK
from retro_live.session import Session
from retro_live.transcriber import transcribe, _receive
from retro_live.whisper_policy import WhisperPolicy


class RetryTests(unittest.TestCase):
    def test_bounds(self):
        for args in ((4,15),(1,0),(True,15),(1,999)):
            with self.assertRaises(ValueError): WhisperPolicy(*args)

    def run_job(self, responses, retries):
        player = VideoPlayer()
        player.set_priority("subtitle")
        player.whisper_policy = WhisperPolicy(retries,5)
        player.jobs.offer((0., np.zeros(1600, dtype=np.float32)))
        player._ended = True
        events = Queue()
        with patch('retro_live.transcriber.Engine') as engine:
            engine.return_value.infer.side_effect = responses
            transcribe(Config(),player,events,Event())
            calls = engine.return_value.infer.call_count
        return player, events, calls

    def test_retry_success(self):
        p, events, calls = self.run_job([TimeoutError(),('result',([],0))],1)
        self.assertEqual(calls,2)
        self.assertEqual(events.get_nowait().kind,'transcription_complete')
        self.assertIsNone(p.ai_active)

    def test_discard_and_release_wait(self):
        p, events, calls = self.run_job([TimeoutError(),TimeoutError()],1)
        self.assertEqual(calls,2)
        p.sound[0] = np.ones((BLOCK,2), dtype=np.float32)
        s = Session(); s.video = p; s.events = events
        self.assertFalse(p._transcription_ready(0,960))
        s.poll()
        self.assertTrue(p._transcription_ready(0,960))
        self.assertEqual(p.ai_expired,1)
        self.assertFalse(p._transcription_ready(BLOCK,960))

    def test_no_retry(self):
        _, events, calls = self.run_job([('failed',('ValueError','test'))],0)
        self.assertEqual(calls,1)
        self.assertEqual(events.get_nowait().kind,'transcription_discarded')

    def test_expired_receive(self):
        p = VideoPlayer()
        with self.assertRaises(TimeoutError):
            _receive(None,None,Event(),p,0)
