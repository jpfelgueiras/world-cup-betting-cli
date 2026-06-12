# World Cup Betting Insights Backend - Production Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install --no-cache-dir -e .

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim as production

LABEL maintainer="World Cup Betting Insights Team"
LABEL description="AI-powered betting insights API for World Cup matches"
LABEL version="0.2.0"

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder --chown=appuser:appgroup /build/src ./src
COPY --from=builder --chown=appuser:appgroup /build/setup.py .
COPY --from=builder --chown=appuser:appgroup /build/README.md .

# Copy configuration files
COPY --chown=appuser:appgroup .env.example .env

# Create necessary directories
RUN mkdir -p /app/data/cache /app/logs && \
    chown -R appuser:appgroup /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    LOG_FILE=/app/logs/app.log \
    LOG_LEVEL=INFO

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Stage 3: Development (optional, use with docker-compose)
# =============================================================================
FROM production as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install dev dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    isort

USER appuser

# Override entrypoint for development
CMD ["python", "-m", "uvicorn", "src.api.app:create_app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
