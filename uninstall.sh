#!/usr/bin/env bash
set -Eeuo pipefail
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
rm -f "$BIN_DIR/retrocast" "$DESKTOP_DIR/retrocast.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
echo 'RetroCast launcher removed. Application files and preferences preserved.'
