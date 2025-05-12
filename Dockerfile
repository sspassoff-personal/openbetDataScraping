# Use a lightweight base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy project files to the working directory
COPY . .

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxrandr2 libasound2 libpangocairo-1.0-0 libxdamage1 libxshmfence1 libgbm1 \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port (optional, useful for debugging or monitoring)
EXPOSE 8080

# Command to run the Python script
CMD ["python", "Play47WebScrape.py"]
