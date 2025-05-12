# Use a lightweight base image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy project files to the working directory
COPY . .

# Install system dependencies (if required by libraries like lxml or cryptography)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip and update
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port (optional, useful for debugging or monitoring)
EXPOSE 8080

# Command to run the Python script
CMD ["python", "Play47WebScrape.py"]

