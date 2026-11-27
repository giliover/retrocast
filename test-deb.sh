#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
source packaging/debian/targets.sh
version=${1:?Usage: test-deb.sh VERSION [TARGET]}
target=${2:-trixie}
[[ $# -le 2 ]] || exit 2
image=$(retrocast_image "$target")
version=$(retrocast_package_version "$version" "$target")
(cd dist && sha256sum -c "retrocast_${version}_amd64.deb.sha256")
# Override the build context ignore file: only the package and smoke test are needed.
context=$(mktemp -d)
trap 'rm -rf -- "$context"' EXIT
mkdir -p "$context/dist" "$context/packaging/debian"
cp "dist/retrocast_${version}_amd64.deb" "$context/dist/"
cp packaging/debian/{Dockerfile.test,smoke-test.sh} "$context/packaging/debian/"
docker buildx build --progress=plain --platform linux/amd64 --build-arg "BASE_IMAGE=$image" --build-arg "VERSION=$version" -f "$context/packaging/debian/Dockerfile.test" "$context"
