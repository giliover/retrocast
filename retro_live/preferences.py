"""Persistent UI preferences in XDG_CONFIG_HOME."""
from .storage import read_json, write_json
import os
from pathlib import Path
from .themes import THEMES
from .i18n import LANGUAGES

class Preferences:
    def __init__(self, path=None):
        base=Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config"))
        self.path=Path(path) if path else base/"retrocast"/"settings.json"
        self.theme="phosphor"
        self.language="en"
        self.load()

    def load(self):
        try:
            obj=read_json(self.path)
            if obj.get("theme") in THEMES: self.theme=obj["theme"]
            if obj.get("language") in LANGUAGES: self.language=obj["language"]
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save(self):
        write_json(self.path, {"theme": self.theme, "language": self.language})
