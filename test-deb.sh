#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
version=${1:?Usage: test-deb.sh VERSION}
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
(cd dist && sha256sum -c "retrocast_${version}_amd64.deb.sha256")
# Override the build context ignore file: only the package and smoke test are needed.
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir -p "$context/dist" "$context/packaging/debian"
cp "dist/retrocast_${version}_amd64.deb" "$context/dist/"
cp packaging/debian/{Dockerfile.test,smoke-test.sh} "$context/packaging/debian/"
docker buildx build --progress=plain --platform linux/amd64 --build-arg "VERSION=$version" -f "$context/packaging/debian/Dockerfile.test" "$context"
