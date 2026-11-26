"""Bounded, deterministic playback choices independent of the graphical toolkit."""
from queue import Queue

DEFAULT_DELAY = 15
PRIORITIES = ('balanced', 'video', 'subtitle')
FPS_CHOICES = (0, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
BALANCED_WAIT = 2.0


class LatestAudioQueue(Queue):
    """Atomic drop-oldest on overflow; retained jobs remain chronological."""
    def offer(self, item):
        with self.not_full:
            dropped = None
            full = self.maxsize > 0 and self._qsize() >= self.maxsize
            if full:
                dropped = self._get()
                self.unfinished_tasks -= 1
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()
            return full, dropped


class WaitPolicy:
    def __init__(self):
        self.since = None
        self.bypassing = False

    def reset(self):
        self.since = None
        self.bypassing = False

    def allows(self, priority, ready, now):
        if ready or priority == 'video':
            self.reset()
            return True
        if priority == 'subtitle':
            return False
        if self.since is None:
            self.since = now
        if now - self.since >= BALANCED_WAIT:
            self.bypassing = True
        return self.bypassing


def effective_fps(source, limit):
    return min(source, limit) if limit else source


class FrameLimiter:
    """Select pictures by media timestamp, without changing the audio clock."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.next_pts = None
        self.limit = None

    def allows(self, pts, limit):
        if not limit:
            self.reset()
            return True
        if self.limit != limit or self.next_pts is None:
            self.limit = limit
            self.next_pts = pts + 1 / limit
            return True
        if pts + 1e-6 < self.next_pts:
            return False
        self.next_pts += (int(max(0., pts - self.next_pts) * limit) + 1) / limit
        return True
