import unittest
from types import SimpleNamespace
from retro_live.packet_buffer import PacketBuffer

class PacketBufferTests(unittest.TestCase):
    def packet(self, key=False, size=10):
        return SimpleNamespace(size=size, is_keyframe=key)

    def test_seek_and_retention(self):
        b=PacketBuffer(seconds=5, max_bytes=1000)
        for i in range(10): b.append(self.packet(i%2==0),i)
        self.assertEqual(b.first,4)
        self.assertEqual(b.seek(7),6)
        self.assertIsNone(b.seek(3))
        self.assertEqual(b.get(6).pts,6)

    def test_byte_and_count_limits(self):
        b=PacketBuffer(max_bytes=35,max_packets=3)
        for i in range(10): b.append(self.packet(True),i)
        self.assertEqual(b.bytes,30)
        self.assertEqual(len(b.entries),3)
        self.assertEqual(b.seek(9),9)
        self.assertFalse(b.append(self.packet(size=36),10))

    def test_reordered_pts(self):
        b=PacketBuffer()
        for i in (0,3,1,2): b.append(self.packet(i==0),i)
        self.assertEqual(b.edge,3)
        self.assertEqual(b.seek(2),0)
