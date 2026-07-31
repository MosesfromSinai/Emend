# Build from the repo root:
#   docker build -f infra/docker/api.Dockerfile --target latex-sandbox .   (works today)
#   docker build -f infra/docker/api.Dockerfile .                          (needs api/)

ARG TECTONIC_VERSION=0.16.9

# ---------------------------------------------------------------- latex-sandbox
FROM python:3.12-slim AS latex-sandbox

ARG TECTONIC_VERSION
ARG TARGETARCH
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && case "$TARGETARCH" in \
         arm64) TRIPLE=aarch64-unknown-linux-musl ;; \
         *)     TRIPLE=x86_64-unknown-linux-musl ;; \
       esac \
    && curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${TRIPLE}.tar.gz" \
       | tar -xz -C /usr/local/bin tectonic \
    && tectonic --version

RUN useradd --create-home appuser
WORKDIR /app

RUN pip install --no-cache-dir "jinja2>=3.1" "pydantic>=2.7"

COPY core/ core/
COPY latex/ latex/
COPY infra/scripts/warm-tectonic-cache.py infra/scripts/warm-tectonic-cache.py

# Pre-warm the Tectonic bundle + fontconfig caches as the runtime user, then
# lock runtime compiles to cache-only (no network egress at compile time).
ENV TECTONIC_CACHE_DIR=/opt/tectonic-cache
RUN mkdir -p "$TECTONIC_CACHE_DIR" && chown -R appuser:appuser "$TECTONIC_CACHE_DIR" /app
USER appuser
RUN python infra/scripts/warm-tectonic-cache.py
ENV TECTONIC_ONLY_CACHED=1 \
    COMPILE_TIMEOUT_SECONDS=10

# --------------------------------------------------------------------- runtime
# NOTE: this stage requires api/ (Workflow B). Until it lands, build with
# --target latex-sandbox.
FROM latex-sandbox AS runtime

USER root
COPY api/ api/
# core/requirements.txt (already copied with core/ above) carries the anthropic
# SDK the real pipeline needs. fly.toml sets MOCK=0, so without it every
# request fails with "anthropic package is required when MOCK=0". Installed
# here rather than in latex-sandbox to keep that stage minimal and offline.
RUN pip install --no-cache-dir -r api/requirements.txt -r core/requirements.txt \
    && chown -R appuser:appuser /app/api
USER appuser

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
