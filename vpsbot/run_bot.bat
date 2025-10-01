@echo off
REM VPS Bot Startup Script for Windows
REM This script helps start the VPS bot with proper environment setup

echo 🚀 Starting VPS Bot...

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please create a .env file with your Discord bot token:
    echo DISCORD_TOKEN=your_bot_token_here
    echo DISCORD_GUILD_ID=your_guild_id_here
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if required directories exist
if not exist "C:\var\lib\vpsbot" (
    echo ❌ VPS bot directories not found!
    echo Please run the setup script first:
    echo python setup_vps.py
    pause
    exit /b 1
)

REM Check if custom Docker image exists
docker image inspect vpsbot-ubuntu:24.04 >nul 2>&1
if errorlevel 1 (
    echo ❌ Custom Docker image not found!
    echo Please run the setup script first:
    echo python setup_vps.py
    pause
    exit /b 1
)

REM Install Python dependencies if needed
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo 📦 Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Start the bot
echo 🤖 Starting Discord bot...
python bot.py

pause
