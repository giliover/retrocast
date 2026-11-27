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
# Resolute's PortAudio requires a reachable PulseAudio server even on import.
# Keep this fixture local to the unprivileged, offline test process.
. /etc/os-release
if [ "${VERSION_CODENAME:-}" = resolute ]; then
    step 'Starting isolated virtual PulseAudio server'
    audio_dir=$(mktemp -d)
    export XDG_RUNTIME_DIR="$audio_dir"
    export PULSE_SERVER="unix:$audio_dir/native"
    export PULSE_SINK=retrocast_test PULSE_SOURCE=retrocast_test.monitor
    pulse_pid=
    cleanup_audio() {
        if [ -n "$pulse_pid" ]; then
            kill "$pulse_pid" 2>/dev/null || :
            wait "$pulse_pid" 2>/dev/null || :
        fi
        rm -rf -- "$audio_dir"
    }
    trap cleanup_audio EXIT
    trap 'exit 1' HUP INT TERM
    pulseaudio -n --daemonize=no --use-pid-file=no --exit-idle-time=-1 \
        --disable-shm=yes --realtime=no --high-priority=no --log-target=stderr \
        -L "module-native-protocol-unix socket=$audio_dir/native" \
        -L 'module-null-sink sink_name=retrocast_test' \
        >"$audio_dir/server.log" 2>&1 &
    pulse_pid=$!
    ready=0
    for attempt in $(seq 1 50); do
        if timeout 2 pactl info >/dev/null 2>&1; then
            ready=1
            break
        fi
        kill -0 "$pulse_pid" 2>/dev/null || break
        sleep 0.2
    done
    if [ "$ready" != 1 ]; then
        cat "$audio_dir/server.log" >&2
        fail 'Virtual PulseAudio server failed to start'
    fi
    pactl set-default-sink retrocast_test
    pactl set-default-source retrocast_test.monitor
    pactl list short sinks
fi
step 'Importing dependencies and initializing UI'
"$interpreter" -X faulthandler - <<'PYTHON'
import importlib
import sys
print(f"Interpreter: {sys.executable}", flush=True)
for name in ("pygame", "av", "numpy", "sounddevice", "faster_whisper", "streamlink"):
    print(f"Importing {name}", flush=True)
    module = importlib.import_module(name)
    print(f"OK: {name} ({getattr(module, '__file__', '?')})", flush=True)
import os
if os.environ.get("PULSE_SINK") == "retrocast_test":
    import sounddevice as sd
    import numpy as np
    print("Testing virtual PortAudio output", flush=True)
    sd.play(np.zeros(800, dtype=np.float32), samplerate=8000, blocking=True)
    print("OK: PortAudio output", flush=True)
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
