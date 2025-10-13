# Multi-stage build for myrtus-monitor
# Stage 1: Build dependencies and application
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv for faster package installation
RUN pip install uv

# Copy the rest of the application code
COPY . /app/

# Accept GitLab token as build argument
ARG GITLAB_TOKEN
ENV GITLAB_TOKEN=${GITLAB_TOKEN}

# Install runtime dependencies
RUN uv sync --no-dev --locked

# Stage 2: Runtime image
FROM python:3.10-slim

# Create a non-root user to run the application
RUN groupadd -g 10001 myrtus && \
    useradd -u 10001 -g myrtus -s /bin/bash -m myrtus

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy installed packages and application from builder
COPY --from=builder /app /app

# Set permissions
RUN chown -R myrtus:myrtus /app

# Create bin directory and symlink for node-monitor
RUN ln -sf /app/.venv/bin/node-monitor /bin/node-monitor && \
    ln -sf /app/.venv/bin/cluster-monitor /bin/cluster-monitor

# Switch to non-root user
USER myrtus
