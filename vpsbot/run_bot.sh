#!/bin/bash

# VPS Bot Startup Script
# This script helps start the VPS bot with proper environment setup

echo "🚀 Starting VPS Bot..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your Discord bot token:"
    echo "DISCORD_TOKEN=your_bot_token_here"
    echo "DISCORD_GUILD_ID=your_guild_id_here"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker first:"
    echo "sudo systemctl start docker"
    exit 1
fi

# Check if required directories exist
if [ ! -d "/var/lib/vpsbot" ]; then
    echo "❌ VPS bot directories not found!"
    echo "Please run the setup script first:"
    echo "sudo python3 setup_vps.py"
    exit 1
fi

# Check if custom Docker image exists
if ! docker image inspect vpsbot-ubuntu:24.04 > /dev/null 2>&1; then
    echo "❌ Custom Docker image not found!"
    echo "Please run the setup script first:"
    echo "sudo python3 setup_vps.py"
    exit 1
fi

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Start the bot
echo "🤖 Starting Discord bot..."
python3 bot.py
