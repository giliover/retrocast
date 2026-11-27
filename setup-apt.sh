#!/usr/bin/env bash
set -euo pipefail

# Configure the RetroCast APT repository on Debian 13 (amd64).
. /etc/os-release
if [[ ${ID:-} != debian || ${VERSION_CODENAME:-} != trixie || $(dpkg --print-architecture) != amd64 ]]; then
    echo 'Supported system: Debian 13 (amd64).' >&2
    exit 1
fi

sudo apt update
sudo apt install -y curl gpg
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
curl --proto '=https' --proto-redir '=https' -fsSL --retry 2 \
    https://giliover.github.io/retrocast/apt/retrocast.gpg -o "$work/retrocast.gpg"
# Require exactly one primary key and verify its full fingerprint.
export GNUPGHOME="$work/gnupg"
mkdir -m 0700 "$GNUPGHOME"
keys=$(gpg --batch --with-colons --show-keys "$work/retrocast.gpg")
mapfile -t fingerprints < <(printf '%s\n' "$keys" | awk -F: '$1=="pub" {primary=1; next} $1=="fpr" && primary {print $10; primary=0}')
if [[ ${#fingerprints[@]} -ne 1 ]]; then
    echo 'Expected exactly one primary signing key.' >&2
    exit 1
fi
printf 'Downloaded key fingerprint: %s\n' "${fingerprints[0]}"
printf 'Enter the official fingerprint obtained from the maintainer: '
read -r expected </dev/tty
expected=${expected//[[:space:]]/}
if [[ ! $expected =~ ^[[:xdigit:]]{40}$ || ${expected^^} != "${fingerprints[0]}" ]]; then
    echo 'Fingerprint mismatch. Repository not configured.' >&2
    exit 1
fi
# Export a binary keyring regardless of the downloaded key encoding.
gpg --batch --import "$work/retrocast.gpg"
gpg --batch --export "${fingerprints[0]}" > "$work/keyring.gpg"
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -o root -g root -m 0644 "$work/keyring.gpg" /etc/apt/keyrings/retrocast.gpg
printf '%s\n' 'deb [arch=amd64 signed-by=/etc/apt/keyrings/retrocast.gpg] https://giliover.github.io/retrocast/apt trixie main' > "$work/retrocast.list"
sudo install -o root -g root -m 0644 "$work/retrocast.list" /etc/apt/sources.list.d/retrocast.list
printf '\nRepository configured. Install RetroCast with:\n  sudo apt update\n  sudo apt install retrocast\n'
