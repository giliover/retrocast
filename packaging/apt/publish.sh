#!/usr/bin/env bash
set -Eeuo pipefail
umask 022
[[ $# == 2 ]] || { echo 'Usage: publish.sh PACKAGE SITE_DIR' >&2; exit 2; }
: "${APT_GPG_FINGERPRINT:?Set signing key fingerprint}"
[[ $APT_GPG_FINGERPRINT =~ ^[A-Fa-f0-9]{40}$ ]]
package=$(realpath -- "$1")
site=$(realpath -m -- "$2")
[[ $(dpkg-deb -f "$package" Package) == retrocast ]]
[[ $(dpkg-deb -f "$package" Architecture) == amd64 ]]
version=$(dpkg-deb -f "$package" Version)
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
repo="$site/apt"
mkdir -p "$repo/conf"
cat > "$repo/conf/distributions" <<CONF
Origin: RetroCast
Label: RetroCast
Codename: trixie
Suite: stable
Architectures: amd64
Components: main
Description: RetroCast packages for Debian 13
SignWith: $APT_GPG_FINGERPRINT
CONF
old=$(reprepro -b "$repo" list trixie retrocast | awk '{print $3}')
if [[ -n $old ]]; then
    dpkg --compare-versions "$version" gt "$old" || { echo "Version must exceed $old" >&2; exit 1; }
fi
reprepro -b "$repo" includedeb trixie "$package"
reprepro -b "$repo" checkpool
reprepro -b "$repo" check trixie
gpg --batch --export "$APT_GPG_FINGERPRINT" > "$repo/retrocast.gpg"
gpgv --keyring "$repo/retrocast.gpg" "$repo/dists/trixie/InRelease"
# GitHub Pages must not process repository files with Jekyll.
touch "$site/.nojekyll"
printf '%s\n' '<!doctype html><html lang="en"><title>RetroCast APT</title><h1>RetroCast APT repository</h1><p>Debian 13 amd64</p></html>' > "$site/index.html"
# Internal database and configuration are excluded from the Pages artifact.
