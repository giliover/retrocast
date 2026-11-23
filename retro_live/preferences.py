"""Persistent UI preferences in XDG_CONFIG_HOME."""
import json
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
            obj=json.loads(self.path.read_text(encoding="utf-8"))
            if obj.get("theme") in THEMES: self.theme=obj["theme"]
            if obj.get("language") in LANGUAGES: self.language=obj["language"]
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp=self.path.with_suffix(".tmp")
        temp.write_text(json.dumps({"theme":self.theme,"language":self.language},indent=2),encoding="utf-8")
        temp.replace(self.path)
