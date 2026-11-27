import subprocess
import threading
import time
import unittest
from unittest.mock import patch
from retro_live.history_status import HistoryStatus, probe

URL='https://www.twitch.tv/example'

class HistoryStatusTests(unittest.TestCase):
    @patch('retro_live.history_status.subprocess.run')
    def test_online_offline_and_unknown(self, run):
        for code, output, error, state in [(0,b'{"streams":{"best":{}}}',b'', 'online'),(0,b'{"streams":{}}',b'', 'offline'),(1,b'{"error":"No playable streams found"}',b'', 'offline'),(1,b'',b'403 forbidden','unknown')]:
            run.return_value=subprocess.CompletedProcess([],code,output,error)
            self.assertEqual(probe(URL)[0],state)
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(run.call_args.kwargs['timeout'],8)
    @patch('retro_live.history_status.subprocess.run')
    def test_timeout_and_unsafe_url(self, run):
        self.assertEqual(probe('http://localhost/')[0],'unknown')
        self.assertEqual(probe(URL+'?token=secret')[0],'unknown')
        run.assert_not_called()
        run.side_effect=subprocess.TimeoutExpired([],8)
        self.assertEqual(probe(URL),('unknown','timeout'))
    def test_nonblocking_dedup_and_cache_expiry(self):
        entered=threading.Event(); release=threading.Event(); calls=[]; now=[100.]
        def check(url):
            calls.append(url); entered.set(); release.wait(2); return 'online','test'
        status=HistoryStatus(checker=check,clock=lambda:now[0])
        try:
            self.assertTrue(status.request([URL],force=True))
            self.assertTrue(entered.wait(1))
            self.assertEqual(status.state(URL),'checking')
            self.assertFalse(status.request([URL]))
            release.set()
            deadline=time.monotonic()+2
            while status.state(URL)!='online' and time.monotonic()<deadline:
                status.poll([URL],True); time.sleep(.01)
            self.assertEqual(status.state(URL),'online')
            self.assertEqual(calls,[URL])
            now[0]+=61
            self.assertFalse(status.poll([URL],True))
            self.assertEqual(status.state(URL),"online")
            self.assertEqual(calls,[URL])
            self.assertTrue(status.request([URL],force=True))
            self.assertIn(URL,status.pending)
        finally:
            release.set(); status.close()
    def test_bounded_pending_and_workers(self):
        release=threading.Event()
        status=HistoryStatus(checker=lambda _: (release.wait(2) and 'online' or 'unknown','test'))
        try:
            status.request([URL+str(i) for i in range(100)])
            self.assertEqual(len(status.pending),30)
            self.assertEqual(len(status.workers),3)
        finally:
            status.close(); release.set()
