"""
Test Setup Script

This script tests the basic functionality of the Real Estate Scraper application
to ensure all components are working correctly.
"""

import sys
import os
import logging
from datetime import datetime
import traceback

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and models"""
    try:
        from database.database_manager import DatabaseManager
        from database.models import PropertyListing, User, Alert, ScrapingLog
        
        db_manager = DatabaseManager()
        logger.info("✅ Database connection successful")
        
        # Test creating tables
        from database.migrations import run_migrations
        if run_migrations():
            logger.info("✅ Database migrations successful")
        else:
            logger.error("❌ Database migrations failed")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_trend_analyzer():
    """Test trend analyzer functionality"""
    try:
        from utils.trend_analyzer import TrendAnalyzer, VIETNAM_LOCATIONS
        
        analyzer = TrendAnalyzer()
        logger.info("✅ Trend analyzer initialized")
        
        # Test trend calculation (with no data, should return empty)
        trends = analyzer.calculate_price_trends()
        logger.info(f"✅ Trend calculation successful (found {len(trends)} trends)")
        
        # Test deal identification (with no data, should return empty)
        deals = analyzer.identify_deals()
        logger.info(f"✅ Deal identification successful (found {len(deals)} deals)")
        
        # Test market insights
        insights = analyzer.get_market_insights()
        logger.info("✅ Market insights calculation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Trend analyzer test failed: {e}")
        return False

def test_auth_service():
    """Test authentication service"""
    try:
        from utils.auth_service import AuthService
        
        auth_service = AuthService()
        logger.info("✅ Auth service initialized")
        
        # Test subscription access rules
        from database.models import User
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="dummy_hash",
            name="Test User",
            subscription_tier="free"
        )
        
        # Test access rules
        can_access_trends = auth_service.check_subscription_access(test_user, 'trends')
        can_access_maps = auth_service.check_subscription_access(test_user, 'maps')
        
        logger.info(f"✅ Auth service tests: trends={can_access_trends}, maps={can_access_maps}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Auth service test failed: {e}")
        return False

def test_payment_service():
    """Test payment service"""
    try:
        from utils.payment_service import PaymentService
        
        payment_service = PaymentService()
        logger.info("✅ Payment service initialized")
        
        # Test getting plans
        plans = payment_service.get_subscription_plans()
        logger.info(f"✅ Payment plans retrieved: {len(plans.get('plans', {}))} plans")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Payment service test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application creation"""
    try:
        from api.app import create_app
        
        app = create_app('development')
        logger.info("✅ Flask app created successfully")
        
        # Test basic endpoints
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                logger.info("✅ Health endpoint working")
            else:
                logger.error("❌ Health endpoint failed")
                return False
            
            # Test API root endpoint
            response = client.get('/')
            if response.status_code == 200:
                logger.info("✅ API root endpoint working")
            else:
                logger.error("❌ API root endpoint failed")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Flask app test failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_scraper_manager():
    """Test scraper manager"""
    try:
        from scraper.scraper_manager import ScraperManager
        
        scraper_manager = ScraperManager()
        logger.info("✅ Scraper manager initialized")
        
        # Test getting stats
        stats = scraper_manager.get_stats()
        logger.info("✅ Scraper stats retrieved")
        
        # Test getting scraper status
        status = scraper_manager.get_scraper_status()
        logger.info(f"✅ Scraper status retrieved: {len(status)} scrapers")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Scraper manager test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Real Estate Scraper tests...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Trend Analyzer", test_trend_analyzer),
        ("Auth Service", test_auth_service),
        ("Payment Service", test_payment_service),
        ("Flask App", test_flask_app),
        ("Scraper Manager", test_scraper_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The application is ready to run.")
        logger.info("\n📝 Next steps:")
        logger.info("1. Run: python app.py --sample-scraping (to test scraping)")
        logger.info("2. Run: python app.py (to start the web server)")
        logger.info("3. Visit: http://localhost:5000 (to see the web interface)")
        logger.info("4. Visit: http://localhost:5000/api (to see the API)")
    else:
        logger.error("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 