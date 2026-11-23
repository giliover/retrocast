"""UI palette registry, independent of playback."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    name: str
    bg: tuple
    panel: tuple
    edge: tuple
    accent: tuple
    text: tuple
    muted: tuple
    warning: tuple
    black: tuple
    scanline: tuple

THEMES = {
    "phosphor": Theme("phosphor", (5,13,10),(10,25,17),(39,110,65),(66,242,119),(180,245,185),(91,152,108),(245,210,90),(2,9,5),(8,20,12)),
    "amber": Theme("amber", (20,13,5),(35,25,12),(115,75,30),(255,186,62),(255,224,164),(162,125,71),(255,112,76),(13,8,3),(28,19,8)),
    "cyan": Theme("cyan", (5,12,19),(12,27,36),(37,91,117),(71,224,246),(191,240,247),(108,158,174),(255,192,96),(3,9,14),(8,20,29)),
    "mono": Theme("mono", (13,13,13),(29,29,29),(90,90,90),(238,238,238),(210,210,210),(143,143,143),(250,190,120),(4,4,4),(20,20,20)),
}

def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["phosphor"])

def next_theme(name: str) -> str:
    keys=list(THEMES)
    return keys[(keys.index(name)+1)%len(keys)] if name in THEMES else keys[0]
