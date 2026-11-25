"""Small private JSON files with bounded reads and atomic replacement."""
import json
import os
import tempfile


def read_json(path, limit=128 * 1024):
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Local settings file too large")
    return json.loads(data)


def write_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".retrocast-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as target:
            json.dump(value, target, ensure_ascii=False)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
