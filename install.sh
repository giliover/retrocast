#!/usr/bin/env bash
set -Eeuo pipefail
SOURCE="${BASH_SOURCE[0]}"
while [[ -h "$SOURCE" ]]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
APP_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
MAIN_SCRIPT="$APP_DIR/app.py"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BIN_TARGET="$BIN_DIR/retrocast"
DESKTOP_FILE="$DESKTOP_DIR/retrocast.desktop"

printf '\nRetroCast installer\n'
for command in python3 ffmpeg; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing dependency: $command" >&2
    exit 1
  fi
done
if [[ ! -f "$MAIN_SCRIPT" || ! -f "$APP_DIR/requirements.txt" ]]; then
  echo 'app.py or requirements.txt not found.' >&2
  exit 1
fi
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
# Streamlink needs fresh plugins for Twitch/YouTube and must be installed
# in THIS venv, regardless of a system-level executable.
echo 'Updating Streamlink inside RetroCast virtualenv (no pip cache)...'
"$VENV_DIR/bin/python" -m pip install --no-cache-dir --upgrade 'streamlink>=7,<9'
echo 'Checking Streamlink runtime...'
"$VENV_DIR/bin/python" -m pip show streamlink >/dev/null
"$VENV_DIR/bin/python" -m streamlink --version
"$VENV_DIR/bin/python" - <<'PYTEST'
import sys, streamlink
print('Streamlink interpreter:', sys.executable)
print('Streamlink module:', streamlink.__file__)
PYTEST
mkdir -p "$BIN_DIR" "$DESKTOP_DIR"
# Quoted heredoc: arguments are passed without shell interpolation at installation time.
cat > "$BIN_TARGET" <<EOF
#!/usr/bin/env bash
set -e
cd $(printf '%q' "$APP_DIR")
exec $(printf '%q' "$VENV_DIR/bin/python") $(printf '%q' "$MAIN_SCRIPT") "\$@"
EOF
chmod +x "$BIN_TARGET"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=RetroCast
GenericName=Live Video Transcriber
Comment=Retro live video player with local transcription
Exec=$BIN_TARGET
Path=$APP_DIR
Icon=video-display
Terminal=false
Categories=AudioVideo;Video;Network;
Keywords=stream;twitch;youtube;transcription;whisper;
StartupNotify=true
EOF
chmod 644 "$DESKTOP_FILE"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
printf '\nInstalled: %s\nDesktop: %s\n' "$BIN_TARGET" "$DESKTOP_FILE"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  printf 'Add to your PATH: export PATH="%s:$PATH"\n' "$BIN_DIR"
fi
printf 'Run: %s\n' "$BIN_TARGET"
printf 'To update Streamlink later: %s -m pip install --no-cache-dir --upgrade streamlink\n' "$VENV_DIR/bin/python"
