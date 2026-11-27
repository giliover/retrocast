#!/usr/bin/env bash
# Shared allowlist for build, smoke test and release.
retrocast_targets() { printf '%s\n' bookworm trixie jammy noble resolute; }
retrocast_image() {
    case "$1" in
        bookworm) echo debian:12-slim ;;
        trixie) echo debian:13-slim ;;
        jammy) echo ubuntu:22.04 ;;
        noble) echo ubuntu:24.04 ;;
        resolute) echo ubuntu:26.04 ;;
        *) echo "Unsupported build target: $1" >&2; return 2 ;;
    esac
}
retrocast_package_version() {
    [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || return 2
    retrocast_image "$2" >/dev/null || return
    printf '%s+%s\n' "$1" "$2"
}
