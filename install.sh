#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $(id -u) != 0 ]] || { echo 'Run as a regular user.' >&2; exit 1; }
APP_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/retrocast"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
for cmd in git python3 ffmpeg flock; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 1; }; done
REPO='https://github.com/giliover/retrocast.git'
[[ $# == 0 ]] || { echo 'Usage: bash install.sh' >&2; exit 2; }
mkdir -p "$ROOT" "$BIN" "$DESKTOP"
# Migrate the legacy repository setting; the updater uses the fixed official URL.
for name in retrocast update_retrocast; do
  tmp=$(mktemp "$BIN/.retrocast.XXXXXXXX")
  install -m 755 "$APP_DIR/lifecycle/$name" "$tmp"
  mv -Tf "$tmp" "$BIN/$name"
done
"$BIN/update_retrocast"
# Desktop Exec quoting per desktop-entry syntax; reject unusual path characters.
if [[ "$BIN" != *'"'* && "$BIN" != *'\'* && "$BIN" != *'%'* && "$BIN" != *'$'* && "$BIN" != *'`'* && "$BIN" != *$'\n'* ]]; then
cat > "$DESKTOP/retrocast.desktop" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=RetroCast
Exec="$BIN/retrocast"
Icon=video-display
Terminal=false
Categories=AudioVideo;Video;Network;
DESKTOP_EOF
fi
printf 'Installed. Run retrocast or update_retrocast from %s\n' "$BIN"
