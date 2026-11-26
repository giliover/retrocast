from dataclasses import dataclass

@dataclass(frozen=True)
class Event:
    kind: str
    value: str | tuple[float, float, str] | tuple[float, float]
