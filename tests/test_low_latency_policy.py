import unittest
from unittest.mock import Mock, patch
from threading import Event
from queue import Queue
import numpy as np
from retro_live.config import Config
from retro_live.player import VideoPlayer, BLOCK
from retro_live.playback_policy import LatestAudioQueue
from retro_live.transcriber import _receive, transcribe
from retro_live.whisper_policy import WhisperPolicy, TIMEOUTS

class LowLatencyTests(unittest.TestCase):
    def test_half_second_options(self):
        self.assertEqual(Config().whisper_timeout, .5)
        self.assertEqual(TIMEOUTS, tuple(i*.5 for i in range(1,121)))
        for v in (0, .25, 60.5, True):
            with self.assertRaises(ValueError): WhisperPolicy(1,v)

    def test_effective_modes(self):
        p = WhisperPolicy(3,.5)
        self.assertEqual(p.effective('balanced').retries,0)
        self.assertEqual(p.playback_timeout('balanced'),0)
        self.assertEqual(p.effective('subtitle').retries,3)
        self.assertEqual(p.playback_timeout('subtitle'),.5)

    def test_newest_and_accounting(self):
        q = LatestAudioQueue(8)
        for i in range(8): q.offer(i)
        latest, dropped = q.newest(q.get_nowait())
        self.assertEqual((latest,dropped),(7,list(range(7))))
        q.task_done()
        self.assertEqual(q.unfinished_tasks,0)

    def test_wait_deadline_only_for_matching_block(self):
        p = VideoPlayer(); p.set_priority('subtitle'); p.whisper_waiting=True; p.position=1
        conn=Mock(); conn.poll.return_value=False
        with patch('retro_live.transcriber.time.monotonic',side_effect=[0.,.25,.5]):
            with self.assertRaises(TimeoutError): _receive(conn,Mock(),Event(),p,30,(0,5,.5))
        p.position=6
        conn.poll.side_effect=[False,True]; conn.recv.return_value=('result',([],0))
        with patch('retro_live.transcriber.time.monotonic',side_effect=[0.,1.]):
            self.assertEqual(_receive(conn,Mock(),Event(),p,30,(0,5,.5)),('result',([],0)))

    def test_balanced_keeps_newest_and_never_retries(self):
        p=VideoPlayer(); p.set_priority('balanced'); p.whisper_policy=WhisperPolicy(3,.5)
        for i in range(3):
            p.jobs.offer((i*.1,np.zeros(1600,dtype=np.float32)))
            p.sound[i]=np.zeros((BLOCK,2),dtype=np.float32)
        p._ended=True; events=Queue()
        with patch('retro_live.transcriber.Engine') as engine:
            engine.return_value.infer.side_effect=TimeoutError()
            transcribe(Config(),p,events,Event())
            self.assertEqual(engine.return_value.infer.call_count,1)
            self.assertEqual(engine.return_value.infer.call_args.args[0],.2)
        self.assertEqual(p.ai_dropped,2)
        self.assertEqual(p.jobs.unfinished_tasks,0)
        self.assertTrue(p._transcription_ready(0,960))

    def test_strict_waits_until_final_result(self):
        p=VideoPlayer(); p.set_priority('subtitle'); p.latest=p.video_latest=15
        p.sound[0]=np.ones((BLOCK,2),dtype=np.float32)
        out=np.zeros((960,2),dtype=np.float32)
        for attempt in (1,2,3):
            p.ai_attempt=attempt; p._callback(out,960,None,None)
            self.assertTrue(p.whisper_waiting)
            self.assertEqual(p._play_sample,0)
            self.assertFalse(out.any())
        p.discard_transcription(0,.1); p._callback(out,960,None,None)
        self.assertTrue(out.any())
        self.assertFalse(p.whisper_waiting)
