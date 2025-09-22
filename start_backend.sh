#!/bin/bash

# Start Backend Server Script for SY Media Downloader

echo "🚀 Starting SY Media Downloader Backend Server..."
echo "================================================"

# Navigate to backend directory
cd webapp/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn yt-dlp python-multipart aiofiles

# Create downloads directory if it doesn't exist
mkdir -p downloads

echo "✅ Backend setup complete!"
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo "================================================"

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
