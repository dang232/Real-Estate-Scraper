# 🚀 Quick Start Guide

Get your Real Estate Scraper running in 5 minutes!

## 📋 Prerequisites

- Python 3.8 or higher
- Git (optional, for version control)

## 🏃‍♂️ Quick Setup

### Windows Users
```bash
# Double-click or run in Command Prompt:
start.bat

# Or use specific commands:
start.bat setup      # Initial setup
start.bat migrate    # Database setup
start.bat test       # Test scraping
start.bat debug      # Start in debug mode
```

### Linux/macOS Users
```bash
# Make script executable (first time only)
chmod +x start.sh

# Run the application:
./start.sh

# Or use specific commands:
./start.sh setup     # Initial setup
./start.sh migrate   # Database setup
./start.sh test      # Test scraping
./start.sh debug     # Start in debug mode
./start.sh help      # Show all commands
```

### Manual Setup (All Platforms)
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install

# 5. Setup environment
cp config.env.example .env
# Edit .env with your settings

# 6. Setup database
python app.py --migrate

# 7. Test scraping
python app.py --sample-scraping

# 8. Start application
python app.py --debug
```

## 🌐 Access the Application

Once running, open your browser and go to:
- **Local**: http://localhost:5000
- **Network**: http://your-ip:5000

## 📊 What You'll See

1. **Dashboard**: Overview of scraped listings
2. **Search**: Filter listings by location, price, area
3. **Export**: Download data as CSV/Excel
4. **API**: REST endpoints for developers

## 🔧 Configuration

Edit `.env` file to customize:
- Database settings
- Email notifications
- Scraping intervals
- Target websites

## 🚨 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.8+ from https://python.org
- Add Python to PATH during installation

**"Dependencies not found"**
```bash
pip install -r requirements.txt
```

**"Playwright browsers not installed"**
```bash
playwright install
```

**"Database migration failed"**
```bash
python -c "from database.migrations import reset_database; reset_database()"
```

**"Port already in use"**
```bash
# Windows: Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :5000
kill -9 <PID>
```

## 📈 Next Steps

1. **Customize scraping**: Edit scraper settings in `.env`
2. **Add email alerts**: Configure SMTP settings
3. **Deploy to production**: See `DEPLOYMENT.md`
4. **Scale up**: Add more target websites

## 🆘 Need Help?

- Check the logs in `logs/` directory
- Review `DEPLOYMENT.md` for detailed instructions
- Check the API documentation at `/api/docs`

---

**🎉 You're all set!** Your Real Estate Scraper is now running and ready to collect data from Vietnamese real estate websites. 