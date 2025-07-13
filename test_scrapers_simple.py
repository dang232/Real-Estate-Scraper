#!/usr/bin/env python3
"""
Simple test script for the updated scrapers
"""

import asyncio
import logging
from scraper.chotot_scraper import ChototScraper
from scraper.batdongsan_scraper import BatDongSanScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_chotot_scraper():
    """Test the updated Chotot scraper"""
    print("Testing Chotot scraper...")
    
    scraper = ChototScraper()
    
    try:
        # Test with limited pages to avoid overwhelming the API
        listings = await scraper.scrape_listings(max_pages=1)
        
        print(f"Chotot scraper found {len(listings)} listings")
        
        if listings:
            # Show first listing details
            first_listing = listings[0]
            print(f"Sample listing:")
            print(f"  Title: {first_listing.title}")
            print(f"  Location: {first_listing.location}")
            print(f"  Price: {first_listing.price:,} VND")
            print(f"  Area: {first_listing.area} m²")
            print(f"  Price/m²: {first_listing.price_per_m2:,.0f} VND")
            print(f"  Type: {first_listing.property_type}")
            print(f"  Link: {first_listing.link}")
            print(f"  Source: {first_listing.source}")
        
        return len(listings) > 0
        
    except Exception as e:
        print(f"Error testing Chotot scraper: {e}")
        return False


async def test_batdongsan_scraper():
    """Test the updated BatDongSan scraper"""
    print("\nTesting BatDongSan scraper...")
    
    scraper = BatDongSanScraper()
    
    try:
        # Test with limited pages
        listings = await scraper.scrape_listings(max_pages=1)
        
        print(f"BatDongSan scraper found {len(listings)} listings")
        
        if listings:
            # Show first listing details
            first_listing = listings[0]
            print(f"Sample listing:")
            print(f"  Title: {first_listing.title}")
            print(f"  Location: {first_listing.location}")
            print(f"  Price: {first_listing.price:,} VND")
            print(f"  Area: {first_listing.area} m²")
            print(f"  Price/m²: {first_listing.price_per_m2:,.0f} VND")
            print(f"  Type: {first_listing.property_type}")
            print(f"  Source: {first_listing.source}")
        
        return len(listings) > 0
        
    except Exception as e:
        print(f"Error testing BatDongSan scraper: {e}")
        return False


async def main():
    """Main test function"""
    print("Testing updated scrapers...")
    print("=" * 50)
    
    # Test Chotot scraper
    chotot_success = await test_chotot_scraper()
    
    # Test BatDongSan scraper
    batdongsan_success = await test_batdongsan_scraper()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Chotot scraper: {'✓ PASS' if chotot_success else '✗ FAIL'}")
    print(f"BatDongSan scraper: {'✓ PASS' if batdongsan_success else '✗ FAIL'}")
    
    if chotot_success and batdongsan_success:
        print("\n🎉 All scrapers are working correctly!")
    else:
        print("\n⚠️  Some scrapers may need attention.")


if __name__ == "__main__":
    asyncio.run(main()) 