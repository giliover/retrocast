#!/usr/bin/env bash
set -Eeuo pipefail
umask 022
[[ $(id -u) != 0 ]] || { echo 'Build as a regular user' >&2; exit 1; }
[[ $# == 2 ]] || { echo 'Usage: build.sh VERSION WHEELHOUSE' >&2; exit 2; }
version=$1
dpkg --validate-version "$version"
[[ $version =~ ^[0-9][a-zA-Z0-9.+~:-]*$ ]] || exit 2
wheelhouse=$(realpath -- "$2")
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$root"
arch=$(dpkg --print-architecture)
py=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
stage=$work/package
mkdir -p "$stage"/{DEBIAN,usr/bin,usr/lib/retrocast/vendor,usr/share/applications}
python3 -m venv "$work/buildenv"
"$work/buildenv/bin/python" -m pip --isolated install --no-index --only-binary=:all: --find-links "$wheelhouse" --target "$stage/usr/lib/retrocast/vendor" -r requirements.txt
cp -r retro_live app.py "$stage/usr/lib/retrocast/"
find "$stage/usr/lib/retrocast" -type d -name __pycache__ -prune -exec rm -rf {} +
sed "s|/usr/bin/python3|/usr/bin/python$py|g" packaging/debian/retrocast > "$stage/usr/bin/retrocast"
chmod 0755 "$stage/usr/bin/retrocast"
install -m644 packaging/debian/retrocast.desktop "$stage/usr/share/applications/retrocast.desktop"
# pip-generated console scripts have build-machine shebangs; application uses python -m instead.
rm -rf "$stage/usr/lib/retrocast/vendor/bin"
cat > "$stage/DEBIAN/control" <<CONTROL
Package: retrocast
Version: $version
Architecture: $arch
Maintainer: ${DEB_MAINTAINER:?Set DEB_MAINTAINER to Name <email>}
Section: video
Priority: optional
Depends: python$py, ffmpeg, libportaudio2, libgl1, libx11-6, libstdc++6, libgomp1
Homepage: https://github.com/giliover/retrocast
Description: Live stream player with automatic subtitles
 Retro-style keyboard-driven player with local Whisper transcription.
CONTROL
mkdir -p dist
out="dist/retrocast_${version//:/_}_${arch}.deb"
dpkg-deb --root-owner-group --build "$stage" "$out"
dpkg-deb --info "$out"
