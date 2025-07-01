FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Create a non-root user to run the application
RUN useradd -m watchkeeper
RUN chown -R watchkeeper:watchkeeper /app
USER watchkeeper

# Command to run the application
CMD ["python", "run.py"]

# Expose port for API server
EXPOSE 8000
