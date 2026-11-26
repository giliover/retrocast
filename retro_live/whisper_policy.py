"""Validated live inference settings; one immutable snapshot per job."""
from dataclasses import dataclass

RETRIES = (0, 1, 2, 3)
TIMEOUTS = tuple(i / 2 for i in range(1, 121))
INFERENCE_HARD_LIMIT = 30.0

@dataclass(frozen=True)
class WhisperPolicy:
    retries: int = 1
    timeout: float = .5

    def __post_init__(self):
        if type(self.retries) is not int or self.retries not in RETRIES:
            raise ValueError('Invalid retry limit')
        if type(self.timeout) not in (int, float) or self.timeout not in TIMEOUTS:
            raise ValueError('Invalid timeout')

    def effective(self, priority):
        return self if priority == 'subtitle' else WhisperPolicy(0, self.timeout)

    def playback_timeout(self, priority):
        return self.timeout if priority == 'subtitle' else 0.0
