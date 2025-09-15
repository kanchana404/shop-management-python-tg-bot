#!/bin/bash

# Production startup script for Telegram Shop Bot

echo "🚀 Starting Telegram Shop Bot in Production Mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and configure your production settings:"
    echo "cp env.example .env"
    echo "Then edit .env with your production values."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the application using Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Show status
echo "📊 Service Status:"
docker-compose ps

echo "✅ Production deployment started!"
echo "📝 To view logs: docker-compose logs -f telegram_bot"
echo "🛑 To stop: docker-compose down"
