#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/retrocast"
BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
[[ -d "$ROOT" ]] || exit 0
exec 9>"$ROOT/lifecycle.lock"
flock -n -x 9 || { echo 'Close RetroCast first.' >&2; exit 1; }
rm -f -- "$BIN/retrocast" "$BIN/update_retrocast" "${XDG_DATA_HOME:-$HOME/.local/share}/applications/retrocast.desktop" "$ROOT/current" "$ROOT/previous" "$ROOT/repository"
rm -rf -- "$ROOT/releases"
echo 'Application removed. Preferences, logs and models preserved.'
