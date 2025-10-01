# Use Ubuntu-based Python 3.8 image to avoid Debian Buster repo issues
FROM python:3.8-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies needed for graphics libraries and curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libice6 \
    curl \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the ports the app runs on
EXPOSE 5000
EXPOSE 8765

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Run the application
CMD ["python", "app.py"]