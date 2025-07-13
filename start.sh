#!/bin/bash

echo "🏠 Real Estate Scraper - Linux/macOS Startup"
echo "============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -d "venv/lib/python*/site-packages/flask" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

# Setup environment file if needed
if [ ! -f ".env" ]; then
    if [ -f "config.env.example" ]; then
        echo "📝 Creating .env file from template..."
        cp config.env.example .env
        echo "⚠️  Please edit .env file with your configuration"
        echo "You can edit it with: nano .env"
    fi
fi

# Check command line arguments
case "$1" in
    "setup")
        echo "🔧 Running initial setup..."
        python start.py --setup
        ;;
    "migrate")
        echo "🗄️  Running database migrations..."
        python start.py --migrate
        ;;
    "test")
        echo "🧪 Running sample scraping test..."
        python start.py --test
        ;;
    "debug")
        echo "🐛 Starting in debug mode..."
        python start.py --debug
        ;;
    "help")
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  setup   - Run initial setup"
        echo "  migrate - Run database migrations"
        echo "  test    - Run sample scraping test"
        echo "  debug   - Start in debug mode"
        echo "  help    - Show this help message"
        echo ""
        echo "Default: Start the application"
        ;;
    *)
        # Default: start the application
        echo "🚀 Starting Real Estate Scraper..."
        python start.py
        ;;
esac 