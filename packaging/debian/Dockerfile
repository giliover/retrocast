FROM debian:13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv dpkg-dev ca-certificates ffmpeg libportaudio2 \
    libgl1 libx11-6 libstdc++6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 builder && \
    install -d -o builder -g builder -m 0755 /home/builder/project
WORKDIR /home/builder/project
COPY --chown=builder:builder . .
USER builder
RUN python3 -m venv /home/builder/venv && \
    /home/builder/venv/bin/python -m pip --isolated download --only-binary=:all: -r requirements.txt -d /home/builder/wheelhouse
RUN --network=none /home/builder/venv/bin/python -m pip --isolated install \
    --no-index --find-links=/home/builder/wheelhouse -r requirements.txt
RUN --network=none /home/builder/venv/bin/python -m unittest discover -s tests -v
ARG VERSION
ARG DEB_MAINTAINER
RUN --network=none DEB_MAINTAINER="$DEB_MAINTAINER" bash packaging/debian/build.sh "$VERSION" /home/builder/wheelhouse
FROM scratch AS export
COPY --from=0 /home/builder/project/dist/ /
