FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY webapp/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY webapp/backend/main.py webapp/backend/helpers.py ./

# Create downloads directory
RUN mkdir -p downloads

# Expose port
EXPOSE 8000

# Start the application
# Cloud Run / Render / Railway inject $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
