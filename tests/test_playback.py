import unittest
import tempfile
from pathlib import Path
import numpy as np
from retro_live.player import VideoPlayer, RATE, BLOCK
from retro_live.storage import read_json, write_json

class PlaybackTests(unittest.TestCase):
    def test_default_delay_and_refill(self):
        p=VideoPlayer(); p.latest=p.video_latest=39
        out=np.ones((960,2),dtype=np.float32)
        p._callback(out,960,None,None)
        self.assertIsNone(p.position); self.assertFalse(out.any())
        p.latest=p.video_latest=40
        p.sound[0]=np.ones((BLOCK,2),dtype=np.float32)
        p._callback(out,960,None,None)
        self.assertEqual(p.position,0); self.assertTrue(np.allclose(out,.8))
        p.set_delay(25); p._callback(out,960,None,None)
        self.assertEqual(p.position,15)
        p.set_delay(500); self.assertEqual(p.delay,120)
        p.set_delay(-5); self.assertEqual(p.delay,10)
    def test_audio_and_inference_share_timestamp(self):
        p=VideoPlayer()
        for i in range(50):
            p._store_audio(np.full((BLOCK,2),.25,dtype=np.float32),i*.1)
        pts,pcm=p.jobs.get_nowait()
        self.assertEqual(pts,0); self.assertEqual(pcm.shape,(80000,))
        self.assertEqual(pcm.dtype,np.float32); self.assertTrue(np.allclose(pcm,.25))
        self.assertAlmostEqual(p.latest,5)
    def test_pause_does_not_advance(self):
        p=VideoPlayer();p.latest=p.video_latest=42
        out=np.ones((960,2),dtype=np.float32)
        p._callback(out,960,None,None); start=p.position
        p.toggle_pause(); p._callback(out,960,None,None)
        self.assertEqual(p.position,start); self.assertFalse(out.any())
    def test_refill_waits_for_new_data(self):
        p=VideoPlayer();p.latest=p.video_latest=40;p._play_sample=40*RATE
        out=np.ones((960,2),dtype=np.float32)
        p._callback(out,960,None,None);self.assertIsNone(p.position)
        p._callback(out,960,None,None);self.assertIsNone(p.position)
        p.latest=p.video_latest=80;p._callback(out,960,None,None)
        self.assertEqual(p.position,40)
    def test_private_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'settings.json';write_json(p,{'value':1})
            self.assertEqual(read_json(p),{'value':1})
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            with self.assertRaises(ValueError):read_json(p,limit=1)
