# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m appuser
WORKDIR /app

# Copy requirement files (create stub if absent to avoid build error)
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

# Upgrade pip & install Python deps
RUN pip install --upgrade pip \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi \
    && if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

# Copy project
COPY . .

USER appuser

# Default command (overrideable)
CMD ["python", "src/main.py"] 