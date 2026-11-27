#!/usr/bin/env bash
set -Eeuo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
version=${1:-0.1.0}
[[ $# -le 1 && $version =~ ^[0-9][a-zA-Z0-9.+~:-]*$ ]] || { echo 'Usage: build-deb.sh [VERSION]' >&2; exit 2; }
: "${DEB_MAINTAINER:?Export DEB_MAINTAINER='Name <email>' first}"
[[ $DEB_MAINTAINER != *$'\n'* && $DEB_MAINTAINER != *$'\r'* ]] || exit 2
command -v docker >/dev/null || { echo 'Docker is required' >&2; exit 1; }
mkdir -p "$root/dist"
docker buildx build --progress=plain --platform linux/amd64 \
    --file "$root/packaging/debian/Dockerfile" \
    --build-arg "VERSION=$version" --build-arg "DEB_MAINTAINER=$DEB_MAINTAINER" \
    --target export --output "type=local,dest=$root/dist" "$root"
package="$root/dist/retrocast_${version//:/_}_amd64.deb"
[[ -s $package ]] || { echo 'Package not generated' >&2; exit 1; }
(cd "$root/dist" && sha256sum -- "${package##*/}" > "${package##*/}.sha256")
printf 'Package: %s\n' "$package"
