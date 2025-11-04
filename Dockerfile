FROM python:3.11-slim

LABEL maintainer="Radar Data Platform"
LABEL description="Autodiscovery microservice for data source discovery"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY contracts/ ./contracts/
COPY README.md ./

# Install package
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p /data/registry /data/mirrors

# Set default environment variables
ENV REGISTRY_PATH=/data/registry/sources_registry.json
ENV MIRRORS_PATH=/data/mirrors
ENV CONTRACTS_PATH=/app/contracts/sources.yml
ENV TIMEOUT_SECS=10
ENV RETRIES=3
ENV USER_AGENT=Autodiscovery/1.0
ENV VERIFY_SSL=true

# Volume for persistent data
VOLUME ["/data"]

# Default command
CMD ["autodiscovery", "--help"]

