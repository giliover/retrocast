#!/usr/bin/env bash
set -euo pipefail

# Select a published base release, not the derivative's marketing version.
select_suite() {
    local base
    case " ${ID:-} ${ID_LIKE:-} " in
        *" debian "*|*" ubuntu "*) ;;
        *) return 1 ;;
    esac
    for base in "${UBUNTU_CODENAME:-}" "${DEBIAN_CODENAME:-}" "${VERSION_CODENAME:-}"; do
        case "$base" in
            bookworm|trixie|jammy|noble|resolute) printf '%s\n' "$base"; return 0 ;;
        esac
    done
    return 1
}
main() {
local expected="@APT_GPG_FINGERPRINT@"
if [[ ! $expected =~ ^[A-Fa-f0-9]{40}$ ]]; then
    echo "Use the published setup script: https://giliover.github.io/retrocast/apt/setup-apt.sh" >&2
    exit 1
fi
. /etc/os-release
if ! command -v apt >/dev/null || ! command -v dpkg >/dev/null || [[ $(dpkg --print-architecture) != amd64 ]]; then
    echo 'APT packages require an amd64 Debian-based system. Use install.sh otherwise.' >&2
    exit 1
fi
if ! suite=$(select_suite); then
    echo 'No compatible APT base identified. Use install.sh for this distribution.' >&2
    exit 1
fi
printf 'RetroCast APT target: %s\n' "$suite"
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
if [[ ! $expected =~ ^[[:xdigit:]]{40}$ || ${expected^^} != "${fingerprints[0]}" ]]; then
    echo 'Fingerprint mismatch. Repository not configured.' >&2
    exit 1
fi
# Export a binary keyring regardless of the downloaded key encoding.
gpg --batch --import "$work/retrocast.gpg"
gpg --batch --export "${fingerprints[0]}" > "$work/keyring.gpg"
# Refuse to configure an unpublished or unsigned suite.
curl --proto '=https' --proto-redir '=https' -fsSL --retry 2 \
    "https://giliover.github.io/retrocast/apt/dists/$suite/InRelease" -o "$work/InRelease"
gpgv --keyring "$work/keyring.gpg" "$work/InRelease"
sudo install -d -m 0755 /etc/apt/keyrings
sudo install -o root -g root -m 0644 "$work/keyring.gpg" /etc/apt/keyrings/retrocast.gpg
printf 'deb [arch=amd64 signed-by=/etc/apt/keyrings/retrocast.gpg] https://giliover.github.io/retrocast/apt %s main\n' "$suite" > "$work/retrocast.list"
sudo install -o root -g root -m 0644 "$work/retrocast.list" /etc/apt/sources.list.d/retrocast.list
printf '\nRepository configured. Install RetroCast with:\n  sudo apt update\n  sudo apt install retrocast\n'
}
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then main "$@"; fi
