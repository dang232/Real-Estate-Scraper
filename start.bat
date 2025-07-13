@echo off
echo Real Estate Scraper - Windows Startup
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Setup environment file if needed
if not exist ".env" (
    if exist "config.env.example" (
        echo Creating .env file from template...
        copy config.env.example .env
        echo Please edit .env file with your configuration
        notepad .env
    )
)

REM Check command line arguments
if "%1"=="setup" (
    echo Running initial setup...
    python start.py --setup
    goto :end
)

if "%1"=="migrate" (
    echo Running database migrations...
    python start.py --migrate
    goto :end
)

if "%1"=="test" (
    echo Running sample scraping test...
    python start.py --test
    goto :end
)

if "%1"=="debug" (
    echo Starting in debug mode...
    python start.py --debug
    goto :end
)

REM Default: start the application
echo Starting Real Estate Scraper...
python start.py

:end
echo.
echo Press any key to exit...
pause >nul 