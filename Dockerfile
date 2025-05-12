# Use a lightweight base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy project files to the working directory
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port (optional, useful for debugging or monitoring)
EXPOSE 8080

# Command to run the Python script
CMD ["python", "Play47WebScrape.py"]
