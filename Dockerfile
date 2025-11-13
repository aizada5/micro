# Base image
FROM python:3.11-slim

# Set working directory to /app
WORKDIR /app

# Install system dependencies for MongoDB SSL
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app folder
COPY app ./app

# Expose port for FastAPI
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
