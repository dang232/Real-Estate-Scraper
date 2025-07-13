#!/usr/bin/env python3
"""
Integration test for scrapers with database and API
"""

import asyncio
import logging
import os
from datetime import datetime

# Import scrapers
from scraper.chotot_scraper import ChototScraper
from scraper.batdongsan_scraper import BatDongSanScraper

# Import database components
from database.database_manager import DatabaseManager
from scraper.scraper_manager import ScraperManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scraper_integration():
    """Test scrapers with database integration"""
    print("Testing scraper integration with database...")
    print("=" * 60)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize scraper manager
    scraper_manager = ScraperManager()
    
    try:
        # Test Chotot scraper
        print("\n1. Testing Chotot scraper...")
        chotot_scraper = ChototScraper()
        chotot_listings = await chotot_scraper.scrape_listings(max_pages=1)
        
        print(f"   ✓ Chotot found {len(chotot_listings)} listings")
        
        # Test BatDongSan scraper
        print("\n2. Testing BatDongSan scraper...")
        batdongsan_scraper = BatDongSanScraper()
        batdongsan_listings = await batdongsan_scraper.scrape_listings(max_pages=1)
        
        print(f"   ✓ BatDongSan found {len(batdongsan_listings)} listings")
        
        # Test database operations
        print("\n3. Testing database operations...")
        
        # Save some listings to database
        total_saved = 0
        
        for listing in chotot_listings[:5]:  # Save first 5 from each scraper
            try:
                saved_listing = db_manager.save_listing(
                    title=listing.title,
                    location=listing.location,
                    price=listing.price,
                    area=listing.area,
                    price_per_m2=listing.price_per_m2,
                    image_url=listing.image_url,
                    link=listing.link,
                    property_type=listing.property_type,
                    bedrooms=listing.bedrooms,
                    bathrooms=listing.bathrooms,
                    source=listing.source
                )
                if saved_listing:
                    total_saved += 1
            except Exception as e:
                logger.error(f"Error saving listing: {e}")
        
        for listing in batdongsan_listings[:5]:
            try:
                saved_listing = db_manager.save_listing(
                    title=listing.title,
                    location=listing.location,
                    price=listing.price,
                    area=listing.area,
                    price_per_m2=listing.price_per_m2,
                    image_url=listing.image_url,
                    link=listing.link,
                    property_type=listing.property_type,
                    bedrooms=listing.bedrooms,
                    bathrooms=listing.bathrooms,
                    source=listing.source
                )
                if saved_listing:
                    total_saved += 1
            except Exception as e:
                logger.error(f"Error saving listing: {e}")
        
        print(f"   ✓ Saved {total_saved} listings to database")
        
        # Test retrieving listings from database
        print("\n4. Testing database retrieval...")
        
        # Get all listings
        all_listings = db_manager.get_listings(limit=10)
        print(f"   ✓ Retrieved {len(all_listings)} listings from database")
        
        # Get listings by source
        chotot_db_listings = db_manager.get_listings(source="Chotot", limit=5)
        batdongsan_db_listings = db_manager.get_listings(source="BatDongSan", limit=5)
        
        print(f"   ✓ Chotot listings in DB: {len(chotot_db_listings)}")
        print(f"   ✓ BatDongSan listings in DB: {len(batdongsan_db_listings)}")
        
        # Test scraper manager
        print("\n5. Testing scraper manager...")
        
        # Get scraper statistics
        stats = scraper_manager.get_stats()
        print(f"   ✓ Scraper stats: {stats}")
        
        # Get scraper status
        status = scraper_manager.get_scraper_status()
        print(f"   ✓ Scraper status: {len(status)} scrapers available")
        
        print("\n" + "=" * 60)
        print("🎉 Integration test completed successfully!")
        print(f"   • Total scraped: {len(chotot_listings) + len(batdongsan_listings)}")
        print(f"   • Total saved: {total_saved}")
        print(f"   • Database listings: {len(all_listings)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        logger.error(f"Integration test error: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoints with scraped data"""
    print("\nTesting API endpoints...")
    print("=" * 60)
    
    try:
        # Import Flask app
        from api.app import app
        
        # Create test client
        with app.test_client() as client:
            # Test listings endpoint
            print("\n1. Testing /api/listings endpoint...")
            response = client.get('/api/listings?limit=5')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✓ Found {data.get('count', 0)} listings via API")
            else:
                print(f"   ❌ API returned status {response.status_code}")
            
            # Test statistics endpoint
            print("\n2. Testing /api/listings/statistics endpoint...")
            response = client.get('/api/listings/statistics')
            if response.status_code == 200:
                stats = response.get_json()
                print(f"   ✓ Statistics: {stats}")
            else:
                print(f"   ❌ Statistics API returned status {response.status_code}")
            
            # Test scraping endpoint
            print("\n3. Testing /api/scraping/status endpoint...")
            response = client.get('/api/scraping/status')
            if response.status_code == 200:
                status = response.get_json()
                print(f"   ✓ Scraping status: {status}")
            else:
                print(f"   ❌ Scraping status API returned status {response.status_code}")
        
        print("\n🎉 API endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API endpoint test failed: {e}")
        logger.error(f"API test error: {e}")
        return False


async def main():
    """Main test function"""
    print("Running integration tests...")
    print("=" * 60)
    
    # Test scraper integration
    scraper_success = await test_scraper_integration()
    
    # Test API endpoints
    api_success = await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("Final Results:")
    print(f"Scraper Integration: {'✓ PASS' if scraper_success else '✗ FAIL'}")
    print(f"API Endpoints: {'✓ PASS' if api_success else '✗ FAIL'}")
    
    if scraper_success and api_success:
        print("\n🎉 All integration tests passed!")
        print("Your real estate scraper is ready for production!")
    else:
        print("\n⚠️  Some integration tests failed. Please check the logs.")


if __name__ == "__main__":
    asyncio.run(main()) 