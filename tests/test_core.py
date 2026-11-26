import unittest
from retro_live.ring import Ring
from retro_live.config import Config
from retro_live.sources import validate_source
from retro_live.pagination import Paginator

class CoreTests(unittest.TestCase):
    def test_ring_order(self):
        r=Ring(3)
        for i in range(7): r.append(i)
        self.assertEqual(list(r), [4,5,6])
        self.assertEqual(r[-1],6)
        self.assertEqual(r[:2],[4,5])
    def test_ring_clear(self):
        r=Ring(2);r.append('a');r.clear();self.assertEqual(len(r),0)
    def test_pagination(self):
        r=Ring(100)
        for i in range(100):r.append(i)
        p=Paginator(page=9,page_size=10)
        self.assertEqual(p.view(r),list(range(90,100)))
    def test_defaults(self):
        c=Config();self.assertEqual(c.delay,15);self.assertEqual(c.language,'auto');self.assertFalse(c.autosave)
    def test_sources(self):
        self.assertEqual(validate_source('https://www.twitch.tv/test'),'https://www.twitch.tv/test')
        for url in ['http://twitch.tv/test','https://127.0.0.1','https://twitch.tv.evil.test','https://user@twitch.tv/test','https://twitch.tv:22/test']:
            with self.subTest(url=url),self.assertRaises(ValueError): validate_source(url)
