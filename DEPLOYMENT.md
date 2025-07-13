# Real Estate Scraper - Deployment Guide

This guide covers how to deploy and run your Real Estate Scraper application in different environments.

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
```bash
# Install Python 3.8+ and pip
python --version  # Should be 3.8 or higher

# Install Git (if not already installed)
git --version
```

### 2. Setup Environment
```bash
# Clone the repository
git clone <your-repo-url>
cd Real-Estate-Scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 3. Configuration
```bash
# Copy environment file
cp config.env.example .env

# Edit .env with your settings
# At minimum, update:
# - SECRET_KEY (generate a random string)
# - SMTP settings (for email alerts)
# - DATABASE_URL (if using different database)
```

### 4. Database Setup
```bash
# Run database migrations
python app.py --migrate

# Or reset database (WARNING: deletes all data)
python -c "from database.migrations import reset_database; reset_database()"
```

### 5. Test the Application
```bash
# Run sample scraping
python app.py --sample-scraping

# Start the application
python app.py --debug

# Access the web interface
# Open http://localhost:5000 in your browser
```

## 🌐 Production Deployment

### Option 1: VPS Deployment (Recommended)

#### 1.1 Server Setup (Ubuntu 20.04+)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Install Node.js (for Playwright)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application user
sudo useradd -m -s /bin/bash scraper
sudo usermod -aG sudo scraper
```

#### 1.2 Application Deployment
```bash
# Switch to application user
sudo su - scraper

# Clone repository
git clone <your-repo-url> /home/scraper/real-estate-scraper
cd /home/scraper/real-estate-scraper

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install

# Setup environment
cp config.env.example .env
# Edit .env for production settings
nano .env

# Run migrations
python app.py --migrate

# Create logs directory
mkdir -p logs
```

#### 1.3 Gunicorn Configuration
```bash
# Install Gunicorn
pip install gunicorn

# Create Gunicorn config
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF
```

#### 1.4 Supervisor Configuration
```bash
# Create supervisor config
sudo tee /etc/supervisor/conf.d/real-estate-scraper.conf << EOF
[program:real-estate-scraper]
command=/home/scraper/real-estate-scraper/venv/bin/gunicorn -c gunicorn.conf.py app:app
directory=/home/scraper/real-estate-scraper
user=scraper
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/scraper/real-estate-scraper/logs/gunicorn.log
EOF

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start real-estate-scraper
```

#### 1.5 Nginx Configuration
```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/real-estate-scraper << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/scraper/real-estate-scraper/ui;
        expires 30d;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/real-estate-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 1.6 SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Docker Deployment

#### 2.1 Create Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5000

# Run migrations and start application
CMD ["sh", "-c", "python app.py --migrate && python app.py --host 0.0.0.0 --port 5000"]
```

#### 2.2 Create docker-compose.yml
```yaml
version: '3.8'

services:
  real-estate-scraper:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=sqlite:///realestate.db
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - real-estate-scraper
    restart: unless-stopped
```

#### 2.3 Deploy with Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 3: Cloud Platform Deployment

#### 3.1 Heroku Deployment
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create runtime.txt
echo "python-3.9.18" > runtime.txt

# Deploy
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

#### 3.2 Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### 3.3 DigitalOcean App Platform
```bash
# Create app.yaml
cat > app.yaml << EOF
name: real-estate-scraper
services:
- name: web
  source_dir: /
  github:
    repo: your-username/real-estate-scraper
    branch: main
  run_command: python app.py --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
EOF

# Deploy via DigitalOcean dashboard or CLI
```

## 🔧 Configuration Management

### Environment Variables
```bash
# Production settings in .env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///realestate.db

# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Scraping settings
SCRAPING_DELAY=5
MAX_PAGES_PER_SITE=20
SCRAPE_INTERVAL_HOURS=6
```

### Database Configuration
```bash
# SQLite (default, good for small deployments)
DATABASE_URL=sqlite:///realestate.db

# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:password@localhost/realestate

# MySQL
DATABASE_URL=mysql://user:password@localhost/realestate
```

## 📊 Monitoring and Maintenance

### 1. Log Management
```bash
# View application logs
tail -f logs/app.log

# View scraping logs
tail -f logs/scraper.log

# View Gunicorn logs
tail -f logs/gunicorn.log
```

### 2. Database Backup
```bash
# SQLite backup
cp realestate.db realestate.db.backup.$(date +%Y%m%d)

# PostgreSQL backup
pg_dump realestate > backup_$(date +%Y%m%d).sql

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/scraper/backups"
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/scraper/real-estate-scraper/realestate.db $BACKUP_DIR/realestate_$DATE.db
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x backup.sh
# Add to crontab: 0 2 * * * /home/scraper/backup.sh
```

### 3. Health Checks
```bash
# Create health check endpoint
curl http://localhost:5000/health

# Monitor scraper status
curl http://localhost:5000/api/scraping/status
```

### 4. Performance Monitoring
```bash
# Install monitoring tools
pip install psutil

# Monitor system resources
htop
df -h
free -h
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Playwright Installation Issues
```bash
# Reinstall Playwright
playwright install --force

# Install system dependencies (Ubuntu)
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

#### 2. Database Migration Errors
```bash
# Reset database
python -c "from database.migrations import reset_database; reset_database()"

# Check database integrity
sqlite3 realestate.db "PRAGMA integrity_check;"
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R scraper:scraper /home/scraper/real-estate-scraper
chmod +x /home/scraper/real-estate-scraper/app.py
```

#### 4. Port Already in Use
```bash
# Find process using port
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

## 📈 Scaling Considerations

### 1. Database Scaling
- Use PostgreSQL for larger datasets
- Implement database connection pooling
- Add read replicas for heavy read loads

### 2. Application Scaling
- Use multiple Gunicorn workers
- Implement load balancing with Nginx
- Consider microservices architecture

### 3. Scraping Scaling
- Implement distributed scraping
- Use proxy rotation
- Add rate limiting and delays

## 🔒 Security Best Practices

### 1. Environment Security
```bash
# Secure environment file
chmod 600 .env

# Use strong secret keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Network Security
```bash
# Configure firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Application Security
- Enable HTTPS
- Implement rate limiting
- Add input validation
- Use secure headers

## 📞 Support and Maintenance

### 1. Regular Maintenance Tasks
```bash
# Weekly tasks
- Check logs for errors
- Monitor disk space
- Update dependencies
- Backup database

# Monthly tasks
- Review performance metrics
- Update SSL certificates
- Security updates
- Code updates
```

### 2. Monitoring Setup
- Set up log monitoring (ELK stack)
- Configure alerting for critical errors
- Monitor system resources
- Track scraping success rates

This deployment guide covers all aspects of getting your Real Estate Scraper running in production. Choose the deployment option that best fits your needs and budget! 