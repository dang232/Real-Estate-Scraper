#!/usr/bin/env python3
"""
Real Estate Scraper - Startup Script

This script provides an easy way to start the Real Estate Scraper application
with different configurations and handles common setup tasks.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import sqlalchemy
        import playwright
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Setup environment file if it doesn't exist"""
    env_file = Path(".env")
    example_file = Path("config.env.example")
    
    if not env_file.exists() and example_file.exists():
        print("📝 Creating .env file from template...")
        subprocess.run(["cp", "config.env.example", ".env"])
        print("✅ Created .env file")
        print("⚠️  Please edit .env file with your configuration")
        return False
    elif env_file.exists():
        print("✅ Environment file exists")
        return True
    else:
        print("❌ No environment template found")
        return False

def run_migrations():
    """Run database migrations"""
    print("🗄️  Running database migrations...")
    try:
        result = subprocess.run([sys.executable, "app.py", "--migrate"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database migrations completed")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def install_playwright():
    """Install Playwright browsers if needed"""
    print("🌐 Checking Playwright installation...")
    try:
        result = subprocess.run(["playwright", "install", "--dry-run"], 
                              capture_output=True, text=True)
        if "No browsers are installed" in result.stdout:
            print("📦 Installing Playwright browsers...")
            subprocess.run(["playwright", "install"])
            print("✅ Playwright browsers installed")
        else:
            print("✅ Playwright browsers already installed")
        return True
    except Exception as e:
        print(f"❌ Playwright error: {e}")
        return False

def run_sample_scraping():
    """Run sample scraping test"""
    print("🔍 Running sample scraping...")
    try:
        result = subprocess.run([sys.executable, "app.py", "--sample-scraping"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Sample scraping completed")
            return True
        else:
            print(f"❌ Sample scraping failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Sample scraping error: {e}")
        return False

def start_application(host="localhost", port=5000, debug=False):
    """Start the application"""
    print(f"🚀 Starting Real Estate Scraper on {host}:{port}")
    print(f"📊 Debug mode: {'Enabled' if debug else 'Disabled'}")
    print(f"🌐 Web interface: http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        cmd = [sys.executable, "app.py", "--host", host, "--port", str(port)]
        if debug:
            cmd.append("--debug")
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Real Estate Scraper Startup")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--setup", action="store_true", help="Run initial setup")
    parser.add_argument("--test", action="store_true", help="Run sample scraping test")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    
    args = parser.parse_args()
    
    print("🏠 Real Estate Scraper - Startup Script")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    if args.setup or not setup_environment():
        if not setup_environment():
            print("\n📋 Setup Instructions:")
            print("1. Edit .env file with your configuration")
            print("2. Run: python start.py --migrate")
            print("3. Run: python start.py --test")
            print("4. Run: python start.py")
            sys.exit(1)
    
    # Install Playwright
    if not install_playwright():
        sys.exit(1)
    
    # Run migrations
    if args.migrate:
        if not run_migrations():
            sys.exit(1)
        return
    
    # Run sample scraping
    if args.test:
        if not run_sample_scraping():
            sys.exit(1)
        return
    
    # Start application
    start_application(args.host, args.port, args.debug)

if __name__ == "__main__":
    main() 