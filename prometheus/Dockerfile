# Use official Prometheus image as base
FROM prom/prometheus:latest

# Switch to root to install additional dependencies
USER root

# Install additional tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /prometheus && \
    mkdir -p /etc/prometheus && \
    mkdir -p /etc/prometheus/rules

# Copy configuration files
COPY prometheus.yml /etc/prometheus/
COPY alerts.yml /etc/prometheus/rules/
COPY recording_rules.yml /etc/prometheus/rules/

# Set permissions
RUN chown -R nobody:nobody /etc/prometheus /prometheus && \
    chmod -R 777 /etc/prometheus /prometheus

# Switch back to nobody user
USER nobody

# Set arguments for prometheus
ARG STORAGE_RETENTION=15d
ARG STORAGE_RETENTION_SIZE=512MB
ARG MAX_BLOCK_DURATION=2h

# Environment variables
ENV STORAGE_RETENTION=$STORAGE_RETENTION \
    STORAGE_RETENTION_SIZE=$STORAGE_RETENTION_SIZE \
    MAX_BLOCK_DURATION=$MAX_BLOCK_DURATION

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9090/-/healthy || exit 1

# Expose port
EXPOSE 9090

# Command to run Prometheus
CMD [ \
    "--config.file=/etc/prometheus/prometheus.yml", \
    "--storage.tsdb.path=/prometheus", \
    "--storage.tsdb.retention.time=${STORAGE_RETENTION}", \
    "--storage.tsdb.retention.size=${STORAGE_RETENTION_SIZE}", \
    "--storage.tsdb.max-block-duration=${MAX_BLOCK_DURATION}", \
    "--web.console.libraries=/usr/share/prometheus/console_libraries", \
    "--web.console.templates=/usr/share/prometheus/consoles", \
    "--web.enable-lifecycle", \
    "--web.enable-admin-api" \
]

# Add metadata
LABEL maintainer="OSRS Discord Bot Team" \
      version="1.0" \
      description="Prometheus instance for OSRS Discord Bot monitoring"
