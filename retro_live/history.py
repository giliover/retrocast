"""Small local history, atomic updates and no stored tokens."""
from .storage import read_json, write_json
import os
from pathlib import Path

class SourceHistory:
    def __init__(self, path=None):
        self.path = Path(path or Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'retrocast' / 'sources.json')
        try:
            value = read_json(self.path)
            if not isinstance(value, list):
                raise ValueError("Invalid history")
            self.items = [x for x in value if isinstance(x, str) and len(x) < 2048][-30:]
        except (OSError, ValueError, TypeError):
            self.items = []

    def add(self, url):
        # Never persist URLs containing credentials or signed query strings.
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.username or parsed.password or (parsed.query and not (parsed.hostname in ('youtube.com','www.youtube.com') and __import__('re').fullmatch(r'v=[A-Za-z0-9_-]{11}', parsed.query))):
            return
        self.items = [x for x in self.items if x != url][-29:] + [url]
        write_json(self.path, self.items)
