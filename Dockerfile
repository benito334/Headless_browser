# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system deps for Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget gnupg ca-certificates fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libxfixes3 libpango-1.0-0 libcairo2 xdg-utils libxkbcommon0 libnss3 libatk-bridge2.0-0 libdrm2 libgbm1 && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Copy source
COPY backend/ ./backend/

# Create mount point for data
VOLUME ["/data"]

ENV PYTHONUNBUFFERED=1
# Install ffmpeg for duration probing
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
