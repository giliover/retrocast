# Debian / Ubuntu packaging

Build and smoke-test each target in its own Docker image. Targets: `bookworm`, `trixie`, `jammy`, `noble`, `resolute` (amd64). Default: `trixie`.

```sh
export DEB_MAINTAINER='Your Name <you@example.org>'
./build-deb.sh 0.1.1 noble
./test-deb.sh 0.1.1 noble
```

Output: `dist/retrocast_0.1.1+noble_amd64.deb` and `.sha256`. The suffix prevents package pool collisions across distributions. The build detects the container's CPython minor version and packages compatible wheels; the installed launcher uses that exact versioned system interpreter (e.g. `/usr/bin/python3.12`). APT installs it if needed. No change to the default Python, no pip during installation. Do not combine wheels from different ABI versions.

Build and test all targets locally:

```sh
source packaging/debian/targets.sh
while read -r target; do
    ./build-deb.sh 0.1.1 "$target" && ./test-deb.sh 0.1.1 "$target" || break
done < <(retrocast_targets)
```

The Docker build downloads wheels, runs unit tests, and packages offline as an unprivileged user. Each target must pass the smoke test before publication. Native dependencies, wheel availability, licenses, real playback and transcription still require validation. Dependencies and base image tags are not pinned. Do not run the Git updater against an APT installation.
