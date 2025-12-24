# Use official Grafana image as base
FROM grafana/grafana:12.3.0-18578466485

# Switch to root to install additional dependencies
USER root

# Install any additional dependencies
RUN apk add --no-cache curl

# Copy configuration files
COPY ./grafana.ini /etc/grafana/grafana.ini
COPY ./provisioning /etc/grafana/provisioning
COPY ./dashboards /etc/grafana/dashboards

# Set permissions
RUN chown -R grafana:root /etc/grafana && \
    chmod -R 777 /etc/grafana && \
    chown -R grafana:root /var/lib/grafana && \
    chmod -R 777 /var/lib/grafana

# Create directories for persistent storage
RUN mkdir -p /var/lib/grafana/dashboards && \
    mkdir -p /var/lib/grafana/plugins && \
    chown -R grafana:root /var/lib/grafana && \
    chmod -R 777 /var/lib/grafana

# Install required plugins
RUN grafana-cli plugins install grafana-piechart-panel && \
    grafana-cli plugins install grafana-worldmap-panel && \
    grafana-cli plugins install grafana-clock-panel && \
    grafana-cli plugins install grafana-simple-json-datasource

# Environment variables
ENV GF_SECURITY_ADMIN_PASSWORD=admin \
    GF_USERS_ALLOW_SIGN_UP=false \
    GF_AUTH_ANONYMOUS_ENABLED=false \
    GF_INSTALL_PLUGINS="grafana-clock-panel,grafana-simple-json-datasource" \
    GF_PATHS_CONFIG="/etc/grafana/grafana.ini" \
    GF_PATHS_DATA="/var/lib/grafana" \
    GF_PATHS_HOME="/usr/share/grafana" \
    GF_PATHS_LOGS="/var/log/grafana" \
    GF_PATHS_PLUGINS="/var/lib/grafana/plugins" \
    GF_PATHS_PROVISIONING="/etc/grafana/provisioning"

# Switch back to grafana user
USER grafana

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Expose port
EXPOSE 3000

# Command to run Grafana
CMD ["grafana-server", \
     "--homepath=/usr/share/grafana", \
     "--config=/etc/grafana/grafana.ini", \
     "cfg:default.paths.data=/var/lib/grafana", \
     "cfg:default.paths.logs=/var/log/grafana", \
     "cfg:default.paths.plugins=/var/lib/grafana/plugins"]
