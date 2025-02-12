# Builder stage with security scanning
FROM python:3.11-slim-bullseye as builder

# Security and build optimizations
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.5.1 \
    PYTHONOPTIMIZE=2

WORKDIR /install

COPY requirements.txt .
COPY security/scan_requirements.sh .

# Enhanced build with security checks
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt \
    && pip install --prefix=/install safety bandit \
    && chmod +x scan_requirements.sh \
    && ./scan_requirements.sh \
    && apt-get purge -y gcc libc6-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add FFmpeg optimization layer
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
        libavfilter-extra \
        libavformat-extra \
        libavutil-extra \
        libavutil-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Production stage
FROM python:3.11-slim-bullseye

# Add security hardening
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        curl \
        tini \
        dumb-init \
        ca-certificates \
        iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --system --group --no-create-home appuser \
    && mkdir -p /app /app/data /app/logs \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

WORKDIR /app
USER appuser

COPY --chown=appuser:appuser . .
COPY --from=builder /install /usr/local

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Runtime optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MALLOC_ARENA_MAX=2 \
    PYTHONMALLOC=malloc

# Add media processing optimizations
ENV FFMPEG_THREAD_QUEUE_SIZE=512 \
    FFMPEG_HWACCEL=auto \
    FFMPEG_PRESET=veryfast

# Use tini as init system
ENTRYPOINT ["/usr/bin/tini", "--", "dumb-init"]

# Enhanced healthcheck with media service check
COPY src/healthcheck.py /app/healthcheck.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

CMD ["python", "-m", "src.bot"]

# Expose metrics and API ports
EXPOSE 9090
EXPOSE 8000
