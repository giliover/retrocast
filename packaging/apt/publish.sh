#!/usr/bin/env bash
set -Eeuo pipefail
umask 022
[[ $# == 3 ]] || { echo 'Usage: publish.sh VERSION PACKAGE_DIR SITE_DIR' >&2; exit 2; }
source "$(dirname -- "${BASH_SOURCE[0]}")/../debian/targets.sh"
: "${APT_GPG_FINGERPRINT:?Set signing key fingerprint}"
[[ $APT_GPG_FINGERPRINT =~ ^[A-Fa-f0-9]{40}$ ]]
version=$1
packages=$(realpath -- "$2")
site=$(realpath -m -- "$3")
repo="$site/apt"
mkdir -p "$repo/conf"
# Validate every artifact before building the repository. Distinct Debian versions
# prevent pool collisions between binary packages built against different ABIs.
while IFS= read -r suite; do
    expected=$(retrocast_package_version "$version" "$suite")
    name="retrocast_${expected}_amd64.deb"
    package="$packages/$name"
    (cd "$packages" && sha256sum -c "$name.sha256")
    [[ $(dpkg-deb -f "$package" Package) == retrocast ]]
    [[ $(dpkg-deb -f "$package" Architecture) == amd64 ]]
    [[ $(dpkg-deb -f "$package" Version) == "$expected" ]]
done < <(retrocast_targets)
: > "$repo/conf/distributions"
while IFS= read -r suite; do
    label=$suite
    [[ $suite != trixie ]] || label=stable # Preserve existing APT Release metadata.
    cat >> "$repo/conf/distributions" <<CONF
Origin: RetroCast
Label: RetroCast
Codename: $suite
Suite: $label
Architectures: amd64
Components: main
Description: RetroCast packages for $suite
SignWith: $APT_GPG_FINGERPRINT

CONF
done < <(retrocast_targets)
gpg --batch --export "$APT_GPG_FINGERPRINT" > "$repo/retrocast.gpg"
[[ -s $repo/retrocast.gpg ]]
while IFS= read -r suite; do
    expected=$(retrocast_package_version "$version" "$suite")
    old=$(reprepro -b "$repo" list "$suite" retrocast | awk '{print $3}')
    if [[ -n $old ]]; then
        dpkg --compare-versions "$expected" gt "$old" || { echo "Version must exceed $old ($suite)" >&2; exit 1; }
    fi
    reprepro -b "$repo" includedeb "$suite" "$packages/retrocast_${expected}_amd64.deb"
    reprepro -b "$repo" check "$suite"
    gpgv --keyring "$repo/retrocast.gpg" "$repo/dists/$suite/InRelease"
done < <(retrocast_targets)
reprepro -b "$repo" checkpool
touch "$site/.nojekyll"
printf '%s\n' '<!doctype html><html lang="en"><title>RetroCast APT</title><h1>RetroCast APT repository</h1><p>Debian and Ubuntu compatible bases (amd64)</p></html>' > "$site/index.html"
# Embed the maintainer-configured public fingerprint in the published installer.
setup_template="$(dirname -- "${BASH_SOURCE[0]}")/../../setup-apt.sh"
sed "s/@APT_GPG_FINGERPRINT@/${APT_GPG_FINGERPRINT^^}/g" "$setup_template" > "$repo/setup-apt.sh"
chmod 0755 "$repo/setup-apt.sh"
bash -n "$repo/setup-apt.sh"
