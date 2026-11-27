#!/bin/sh
set -eu
[ "$(id -u)" != 0 ]
[ "$(dpkg-query -W -f='${Version}' retrocast)" = "$1" ]
[ -x /usr/bin/retrocast ]
[ ! -w /usr/lib/retrocast ]
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/usr/lib/retrocast/vendor:/usr/lib/retrocast
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
interpreter=$(sed -n 's|^exec \(/usr/bin/python3\.[0-9][0-9]*\) /usr/lib/retrocast/app.py .*|\1|p' /usr/bin/retrocast)
[ -n "$interpreter" ] && [ -x "$interpreter" ]
"$interpreter" - <<'PY'
import pygame, av, numpy, sounddevice, faster_whisper, streamlink
from retro_live.ui import RetroUI
pygame.init()
pygame.display.set_mode((320, 240))
pygame.quit()
PY
"$interpreter" -m streamlink --version
ffmpeg -version
