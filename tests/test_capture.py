import subprocess
import sys
import threading
import unittest
from unittest.mock import patch
from retro_live.capture import StreamCapture


class CaptureTests(unittest.TestCase):
    def test_pipe_and_cleanup(self):
        real_popen = subprocess.Popen
        capture = StreamCapture()
        with patch('retro_live.capture.subprocess.Popen', side_effect=lambda *a, **kw: real_popen([sys.executable, '-c', 'import sys; sys.stdout.buffer.write(b"media")'], **kw)) as mock:
            try:
                source = capture.start('https://www.twitch.tv/example', 'best', threading.Event())
                self.assertEqual(source.read(), b'media')
                args = mock.call_args.args[0]
                self.assertIn('--stdout', args)
                self.assertNotIn('--stream-url', args)
                self.assertFalse(mock.call_args.kwargs['shell'])
            finally:
                capture.close()
            self.assertTrue(source.closed)

    def test_invalid_input_never_spawns(self):
        with patch('retro_live.capture.subprocess.Popen') as mock:
            with self.assertRaises(ValueError):
                StreamCapture().start('http://localhost/', 'best', threading.Event())
            with self.assertRaises(ValueError):
                StreamCapture().start('https://www.twitch.tv/example', '--help', threading.Event())
            mock.assert_not_called()

    def test_stop_before_start(self):
        stop = threading.Event(); stop.set()
        with patch('retro_live.capture.subprocess.Popen') as mock:
            self.assertIsNone(StreamCapture().start('https://www.twitch.tv/example', 'best', stop))
            mock.assert_not_called()
