"""Bounded compressed video history. All access is protected by the player lock."""
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class PacketEntry:
    packet: object
    pts: float
    size: int
    key: bool


class PacketBuffer:
    def __init__(self, seconds=140, max_bytes=256*1024*1024, max_packets=24000):
        self.seconds = seconds
        self.max_bytes = max_bytes
        self.max_packets = max_packets
        self.entries = {}
        self.keys = deque()
        self.first = self.next = self.bytes = 0
        self.edge = -1.0

    def append(self, packet, pts):
        size = int(packet.size)
        if size <= 0 or size > self.max_bytes:
            return False
        index = self.next
        self.next += 1
        entry = PacketEntry(packet, pts, size, bool(packet.is_keyframe))
        self.entries[index] = entry
        self.bytes += size
        self.edge = max(self.edge, pts)
        if entry.key:
            self.keys.append((index, pts))
        while self.entries and (self.bytes > self.max_bytes or len(self.entries) > self.max_packets or self.entries[self.first].pts < self.edge-self.seconds):
            self.bytes -= self.entries.pop(self.first).size
            if self.keys and self.keys[0][0] == self.first:
                self.keys.popleft()
            self.first += 1
        return True

    def seek(self, pts):
        # Only on startup/seek, never on each UI refresh. O(number of GOPs).
        result = None
        for index, stamp in self.keys:
            if stamp > pts:
                break
            result = index
        return result

    def get(self, index):
        return self.entries.get(index)
