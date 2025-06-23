# Use multi-stage build for a smaller, more secure final image

# 1. Builder Stage: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition
COPY pyproject.toml README.md LICENSE ./

# Build wheel files for all production dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels .

# 2. Final Stage: Production image
FROM python:3.11-slim

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash botuser

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from the builder stage
COPY --from=builder /app/wheels /wheels

# Install the wheels
RUN pip install --no-cache-dir /wheels/*

# Copy the application source code
COPY ./src ./src

# Change ownership to the non-root user
RUN chown -R botuser:botuser /app

# Switch to the non-root user
USER botuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default command to run the application
CMD ["python", "-m", "src.main"]
