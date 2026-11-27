#!/bin/sh
set -eu
fail() { printf 'SMOKE ERROR: %s\n' "$*" >&2; exit 1; }
step() { printf '\nSMOKE: %s\n' "$*"; }
step 'Checking package and permissions'
[ "$(id -u)" != 0 ] || fail 'Smoke test must run unprivileged'
installed=$(dpkg-query -W -f='${Version}' retrocast)
[ "$installed" = "$1" ] || fail "Expected $1, installed $installed"
[ -x /usr/bin/retrocast ] || fail 'Launcher missing or not executable'
[ ! -w /usr/lib/retrocast ] || fail 'Application directory is writable'
unset PYTHONHOME PYTHONPATH
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/usr/lib/retrocast/vendor:/usr/lib/retrocast
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
step 'Checking packaged Python interpreter'
interpreter=$(sed -n 's|^exec \(/usr/bin/python3\.[0-9][0-9]*\) /usr/lib/retrocast/app.py .*|\1|p' /usr/bin/retrocast)
[ -n "$interpreter" ] || fail 'Could not identify launcher interpreter'
[ -x "$interpreter" ] || fail "Interpreter not executable: $interpreter"
"$interpreter" -VV
step 'Importing dependencies and initializing UI'
"$interpreter" -X faulthandler - <<'PYTHON'
import importlib
import sys
print(f"Interpreter: {sys.executable}", flush=True)
for name in ("pygame", "av", "numpy", "sounddevice", "faster_whisper", "streamlink"):
    print(f"Importing {name}", flush=True)
    module = importlib.import_module(name)
    print(f"OK: {name} ({getattr(module, '__file__', '?')})", flush=True)
print("Importing RetroUI", flush=True)
from retro_live.ui import RetroUI
import pygame
print("Initializing pygame", flush=True)
pygame.init()
try:
    print("Opening dummy display", flush=True)
    pygame.display.set_mode((320, 240))
finally:
    pygame.quit()
print("OK: UI", flush=True)
PYTHON
step 'Checking Streamlink CLI'
"$interpreter" -X faulthandler -m streamlink --version
step 'Checking FFmpeg CLI'
ffmpeg -version
step 'All smoke checks passed'
