FROM python:3.10-slim-bookworm AS bento4

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip \
    && rm -rf /var/lib/apt/lists/*
RUN curl --fail --show-error --silent --location \
      https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip \
      --output /tmp/bento4.zip \
    && unzip -j /tmp/bento4.zip '*/bin/mp4decrypt' '*/bin/mp4dump' -d /usr/local/bin

FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WINEARCH=win64 \
    WINEDEBUG=-all

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        aria2 dialog ffmpeg mediainfo mkvtoolnix wine wine64 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=bento4 /usr/local/bin/mp4decrypt /usr/local/bin/mp4dump /usr/local/bin/

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p configs/KEYS

ENTRYPOINT ["/bin/sh", "/app/docker/entrypoint.sh"]
