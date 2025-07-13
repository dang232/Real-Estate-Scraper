"""
Chotot Scraper

This module implements scraping functionality for chotot.com using their internal API
"""

import asyncio
import logging
import json
import requests
from typing import List, Optional, Any, Dict
from datetime import datetime
from urllib.parse import urljoin, urlencode
import aiohttp

from .base_scraper import BaseScraper, PropertyListing

logger = logging.getLogger(__name__)


class ChototScraper(BaseScraper):
    """
    Scraper for chotot.com using their internal API
    
    This scraper uses the gateway.chotot.com API endpoint to fetch listings
    more efficiently than browser scraping.
    """
    
    def __init__(self):
        super().__init__(
            name="Chotot",
            base_url="https://chotot.com",
            delay_range=(1, 2)  # API requests can be faster
        )
        
        # API endpoint
        self.api_url = "https://gateway.chotot.com/v1/public/ad-listing"
        
        # Default headers for API requests
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://chotot.com/',
            'Origin': 'https://chotot.com',
            'Content-Type': 'application/json',
        }
        
        # Region mappings for API (updated with proper codes)
        self.regions = {
            'hanoi': '12000',
            'hochiminh': '13000',
            'danang': '15000',
            'cantho': '16000',
            'haiphong': '14000',
            'binhduong': '18000',
            'dongnai': '19000',
            'vungtau': '20000',
        }
        
        # Category codes
        self.categories = {
            'real_estate': '1000',
            'apartment': '1001',
            'house': '1002',
            'land': '1003',
            'office': '1004',
        }
    
    async def scrape_listings(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Scrape property listings from Chotot using their API
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        listings = []
        
        # Scrape from multiple regions
        for region_name, region_code in self.regions.items():
            logger.info(f"Scraping Chotot listings for region: {region_name} ({region_code})")
            
            try:
                region_listings = await self._scrape_region(region_code, max_pages)
                listings.extend(region_listings)
                await self.respectful_delay()
                
            except Exception as e:
                logger.error(f"Error scraping region {region_name}: {e}")
                continue
        
        logger.info(f"Total Chotot listings scraped: {len(listings)}")
        return listings
    
    async def _scrape_region(self, region_code: str, max_pages: int) -> List[PropertyListing]:
        """
        Scrape listings for a specific region
        
        Args:
            region_code: Chotot region code (e.g., "13000" for TP.HCM)
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        listings = []
        page = 1
        
        while page <= max_pages:
            try:
                logger.info(f"Scraping Chotot page {page} for region {region_code}")
                
                # API parameters
                params = {
                    "region_v2": region_code,
                    "cg": self.categories['real_estate'],  # Real estate category
                    "limit": "20",
                    "page": str(page),
                    "st": "s",  # sell listings
                }
                
                # Make API request
                response = requests.get(self.api_url, params=params, headers=self.api_headers, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"API request failed with status {response.status_code} for page {page}")
                    break
                
                data = response.json()
                ads = data.get("ads", [])
                
                if not ads:
                    logger.info(f"No more ads found on page {page}")
                    break
                
                # Parse each ad
                for ad in ads:
                    try:
                        listing = self._parse_api_listing(ad)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        logger.error(f"Error parsing ad: {e}")
                        continue
                
                # Check if we have more pages
                if len(ads) < 20:  # Less than limit means last page
                    break
                
                page += 1
                await self.respectful_delay()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on page {page} for region {region_code}: {e}")
                break
            except Exception as e:
                logger.error(f"Error scraping page {page} for region {region_code}: {e}")
                break
        
        return listings
    
    def _parse_api_listing(self, ad_data: Dict[str, Any]) -> Optional[PropertyListing]:
        """
        Parse a listing from the API response
        
        Args:
            ad_data: Raw ad data from API
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None
        """
        try:
            # Extract basic information
            title = ad_data.get('subject', 'No title')
            list_id = ad_data.get('list_id', '')
            
            # Extract price
            price = self._extract_price(ad_data)
            
            # Extract area
            area = self._extract_area(ad_data)
            
            # Extract location
            location = self._extract_location(ad_data)
            
            # Extract image
            image_url = self._extract_image(ad_data)
            
            # Extract link
            link = f"https://www.chotot.com/{list_id}" if list_id else ""
            
            # Extract property type
            property_type = self._extract_property_type(ad_data)
            
            # Extract bedrooms and bathrooms
            bedrooms = self._extract_bedrooms(ad_data)
            bathrooms = self._extract_bathrooms(ad_data)
            
            # Calculate price per m²
            price_per_m2 = self.calculate_price_per_m2(price, area)
            
            # Create PropertyListing object
            listing = PropertyListing(
                title=title.strip(),
                location=location.strip(),
                price=price,
                area=area,
                price_per_m2=price_per_m2,
                image_url=image_url,
                link=link,
                property_type=property_type.strip(),
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                timestamp=datetime.now(),
                source=self.name,
                raw_data=ad_data
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Error parsing API listing: {e}")
            return None
    
    def _extract_price(self, ad_data: Dict[str, Any]) -> float:
        """Extract price from ad data"""
        price_info = ad_data.get('price', {})
        if isinstance(price_info, dict):
            # API returns price as object with value
            price_value = price_info.get('value', 0)
            if price_value:
                return float(price_value)
        
        # Fallback to price_string
        price_string = ad_data.get('price_string', '0')
        return self.clean_price(price_string)
    
    def _extract_area(self, ad_data: Dict[str, Any]) -> float:
        """Extract area from ad data"""
        # Try different area fields
        area_fields = ['area', 'size', 'square_meter']
        for field in area_fields:
            area_value = ad_data.get(field)
            if area_value:
                if isinstance(area_value, (int, float)):
                    return float(area_value)
                elif isinstance(area_value, str):
                    return self.clean_area(area_value)
        
        # Fallback to size_string
        size_string = ad_data.get('size_string', '0')
        return self.clean_area(size_string)
    
    def _extract_location(self, ad_data: Dict[str, Any]) -> str:
        """Extract location from ad data"""
        region_name = ad_data.get('region_name', '')
        area_name = ad_data.get('area_name', '')
        
        if region_name and area_name:
            return f"{area_name}, {region_name}"
        elif region_name:
            return region_name
        elif area_name:
            return area_name
        
        # Fallback to other location fields
        location_fields = ['location', 'address']
        for field in location_fields:
            location_value = ad_data.get(field)
            if location_value:
                return str(location_value)
        
        return "Unknown"
    
    def _extract_image(self, ad_data: Dict[str, Any]) -> Optional[str]:
        """Extract image URL from ad data"""
        images = ad_data.get('images', [])
        if images and len(images) > 0:
            # Get the first image
            image_data = images[0]
            if isinstance(image_data, dict):
                return image_data.get('url') or image_data.get('src')
            elif isinstance(image_data, str):
                return image_data
        
        return None
    
    def _extract_property_type(self, ad_data: Dict[str, Any]) -> str:
        """Extract property type from ad data"""
        # Try different type fields
        type_fields = ['category_name', 'type', 'property_type']
        for field in type_fields:
            type_value = ad_data.get(field)
            if type_value:
                return str(type_value)
        
        return "Unknown"
    
    def _extract_bedrooms(self, ad_data: Dict[str, Any]) -> Optional[int]:
        """Extract number of bedrooms from ad data"""
        # Try different bedroom fields
        bedroom_fields = ['bedroom', 'bedrooms', 'phong_ngu']
        for field in bedroom_fields:
            bedroom_value = ad_data.get(field)
            if bedroom_value:
                if isinstance(bedroom_value, (int, float)):
                    return int(bedroom_value)
                elif isinstance(bedroom_value, str):
                    import re
                    numbers = re.findall(r'\d+', bedroom_value)
                    if numbers:
                        return int(numbers[0])
        
        return None
    
    def _extract_bathrooms(self, ad_data: Dict[str, Any]) -> Optional[int]:
        """Extract number of bathrooms from ad data"""
        # Try different bathroom fields
        bathroom_fields = ['bathroom', 'bathrooms', 'phong_tam']
        for field in bathroom_fields:
            bathroom_value = ad_data.get(field)
            if bathroom_value:
                if isinstance(bathroom_value, (int, float)):
                    return int(bathroom_value)
                elif isinstance(bathroom_value, str):
                    import re
                    numbers = re.findall(r'\d+', bathroom_value)
                    if numbers:
                        return int(numbers[0])
        
        return None
    
    def parse_listing(self, listing_element: Any) -> Optional[PropertyListing]:
        """
        Parse a single listing element (kept for compatibility)
        
        Args:
            listing_element: Raw listing element from the page
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None if parsing fails
        """
        # This method is kept for compatibility but the API version is preferred
        logger.warning("Using synchronous parse_listing - API version is preferred")
        return None


# Sample data for testing and development
SAMPLE_CHOTOT_DATA = [
    {
        "title": "Căn hộ cao cấp tại Quận 2, TP.HCM",
        "location": "Quận 2, TP.HCM",
        "price": 3200000000,  # 3.2 billion VND
        "area": 85.0,  # 85 m²
        "price_per_m2": 37647058.82,
        "image_url": "https://example.com/chotot-image1.jpg",
        "link": "https://chotot.com/mua-ban-nha-dat/can-ho-cao-cap-quan-2",
        "property_type": "Căn hộ",
        "bedrooms": 3,
        "bathrooms": 2,
        "timestamp": datetime.now(),
        "source": "Chotot",
        "raw_data": {
            "price_text": "3.2 tỷ",
            "area_text": "85m²",
            "property_type": "Căn hộ"
        }
    },
    {
        "title": "Nhà riêng 4 tầng tại Quận 7, TP.HCM",
        "location": "Quận 7, TP.HCM",
        "price": 8500000000,  # 8.5 billion VND
        "area": 150.0,  # 150 m²
        "price_per_m2": 56666666.67,
        "image_url": "https://example.com/chotot-image2.jpg",
        "link": "https://chotot.com/mua-ban-nha-dat/nha-rieng-4-tang-quan-7",
        "property_type": "Nhà riêng",
        "bedrooms": 4,
        "bathrooms": 3,
        "timestamp": datetime.now(),
        "source": "Chotot",
        "raw_data": {
            "price_text": "8.5 tỷ",
            "area_text": "150m²",
            "property_type": "Nhà riêng"
        }
    }
] 