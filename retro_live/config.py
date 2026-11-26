from dataclasses import dataclass
from pathlib import Path
from .playback_policy import DEFAULT_DELAY

@dataclass
class Config:
    url: str = ''
    quality: str = 'auto'
    model: str = 'base'
    language: str = 'auto'
    delay: int = DEFAULT_DELAY
    priority: str = "balanced"
    fps_limit: int = 0
    whisper_retries: int = 1
    whisper_timeout: float = .5
    chunk: float = 5.0
    device: str = 'auto'
    compute_type: str = 'default'
    output: Path = Path('transcricao.txt')
    autosave: bool = False
    # Reserve CPU capacity for PyAV and the Pygame UI.
    whisper_cpu_threads: int = 0  # nproc (minimum 1) unless overridden
    whisper_num_workers: int = 0  # Auto: half of nproc (minimum 1)
