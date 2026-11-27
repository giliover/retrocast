# Debian packaging (experimental)

Build on the target Debian release and architecture (initial target: Debian 13 amd64). Use a clean non-root build environment. No network is used by the package build; prepare the wheelhouse separately and review/pin all wheels and hashes before publishing. The existing requirements are intentionally unchanged.

```sh
sudo apt install python3 python3-venv python3-pip dpkg-dev
python3 -m venv /tmp/retrocast-build-env
/tmp/retrocast-build-env/bin/pip download --only-binary=:all: -r requirements.txt -d wheelhouse
export DEB_MAINTAINER='Your Name <your-email@example.org>'
bash packaging/debian/build.sh 0.1.0 wheelhouse
sudo apt install ./dist/retrocast_0.1.0_amd64.deb
/usr/bin/retrocast
sudo apt remove retrocast
```

Version is illustrative. Wheel availability, native library dependencies, license redistribution, and runtime behavior must be verified on a clean Debian target before release. If a wheel is unavailable, build it separately from reviewed sources. Do not mix wheels from different Python ABIs. Do not run the Git updater on the Debian installation; remove any old user-local launcher if it shadows /usr/bin/retrocast. User data is preserved by apt remove. No maintainer scripts or pip operations run during installation. This is a private-repository packaging approach, not a Debian official archive submission.

## Docker (Debian 13 / amd64)

Requires Docker with Buildx. From the project root:

```sh
export DEB_MAINTAINER='Your Name <you@example.org>'
./build-deb.sh 0.1.0
```

The image downloads wheels, runs unit tests and packages offline as an unprivileged user. Buildx exports the package directly to `dist/`, alongside a SHA-256 checksum. No privileged container or Docker socket mount is needed. Install on Debian 13 with `sudo apt install ./dist/retrocast_0.1.0_amd64.deb`. Dependencies are not pinned; wheel availability and native runtime compatibility must be verified before publishing. The base image tag is mutable. Docker builds require network access for apt and wheel download only.
