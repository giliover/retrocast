"""Small local history, atomic updates and no stored tokens."""
import json
import os
from pathlib import Path

class SourceHistory:
    def __init__(self, path=None):
        self.path = Path(path or Path.home() / '.config' / 'retrocast' / 'sources.json')
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))
            self.items = [x for x in value if isinstance(x, str) and len(x) < 2048][-30:]
        except (OSError, ValueError, TypeError):
            self.items = []

    def add(self, url):
        # Never persist URLs containing credentials or signed query strings.
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.username or parsed.password or parsed.query and any(
            word in parsed.query.lower() for word in ('token=', 'signature=', 'auth=', 'key=')
        ):
            return
        self.items = [x for x in self.items if x != url][-29:] + [url]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.items, indent=2), encoding='utf-8')
        os.replace(temp, self.path)
