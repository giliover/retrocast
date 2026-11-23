from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    url: str = ''
    quality: str = 'best'
    model: str = 'base'
    language: str = 'pt'
    chunk: float = 5.0
    device: str = 'auto'
    compute_type: str = 'default'
    output: Path = Path('transcricao.txt')
    autosave: bool = True
    # Reserve CPU capacity for PyAV and the Pygame UI.
    whisper_cpu_threads: int = 0  # nproc (minimum 1) unless overridden
    whisper_num_workers: int = 0  # Auto: half of nproc (minimum 1)
