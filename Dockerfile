# Production Dockerfile for KESHAV AI
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for health check, espeak for speech)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    espeak \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Environment variables
ENV PORT=8550
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8550

# Run KESHAV AI in web mode on 0.0.0.0
CMD ["python", "main.py", "--web"]
