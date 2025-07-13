"""
BatDongSan Scraper

This module implements scraping functionality for batdongsan.com.vn
"""

import asyncio
import logging
from typing import List, Optional, Any
from datetime import datetime
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page

from .base_scraper import BaseScraper, PropertyListing

logger = logging.getLogger(__name__)


class BatDongSanScraper(BaseScraper):
    """
    Scraper for batdongsan.com.vn
    
    This scraper handles the specific structure and selectors
    used by the BatDongSan website with fallback selectors.
    """
    
    def __init__(self):
        super().__init__(
            name="BatDongSan",
            base_url="https://batdongsan.com.vn",
            delay_range=(3, 6)  # Slightly longer delays for this site
        )
        
        # Primary CSS selectors for BatDongSan (updated)
        self.selectors = {
            'listing_container': [
                '.vip-item, .normal-item',
                '.re-item',
                '.property-item',
                '.listing-item',
                '.product-item',
                '[data-component="property-item"]',
                '.item',
                '.card',
                '.listing-card'
            ],
            'title': [
                '.vip-item-title a, .normal-item-title a',
                '.re-title a',
                '.property-title a',
                '.listing-title a',
                '.product-title a',
                'h3 a, h2 a',
                'a[href*="/ban-"], a[href*="/cho-thue-"]',
                '.title a',
                '.name a'
            ],
            'price': [
                '.vip-item-price, .normal-item-price',
                '.re-price',
                '.property-price',
                '.listing-price',
                '.product-price',
                '.price',
                '[class*="price"]',
                '.cost',
                '.value'
            ],
            'area': [
                '.vip-item-area, .normal-item-area',
                '.re-area',
                '.property-area',
                '.listing-area',
                '.product-area',
                '.area',
                '[class*="area"]',
                '.size',
                '.square'
            ],
            'location': [
                '.vip-item-location, .normal-item-location',
                '.re-location',
                '.property-location',
                '.listing-location',
                '.product-location',
                '.location',
                '[class*="location"]',
                '.address',
                '.place'
            ],
            'image': [
                '.vip-item-image img, .normal-item-image img',
                '.re-image img',
                '.property-image img',
                '.listing-image img',
                '.product-image img',
                'img[src*="batdongsan"]',
                '.thumbnail img',
                '.photo img',
                'img'
            ],
            'property_type': [
                '.vip-item-type, .normal-item-type',
                '.re-type',
                '.property-type',
                '.listing-type',
                '.product-type',
                '.type',
                '[class*="type"]',
                '.category',
                '.kind'
            ],
            'bedrooms': [
                '.vip-item-bedroom, .normal-item-bedroom',
                '.re-bedroom',
                '.property-bedroom',
                '.listing-bedroom',
                '.product-bedroom',
                '.bedroom',
                '[class*="bedroom"]',
                '.phong-ngu',
                '.room'
            ],
            'bathrooms': [
                '.vip-item-bathroom, .normal-item-bathroom',
                '.re-bathroom',
                '.property-bathroom',
                '.listing-bathroom',
                '.product-bathroom',
                '.bathroom',
                '[class*="bathroom"]',
                '.phong-tam',
                '.wc'
            ],
            'next_page': [
                '.pagination .next a',
                '.pagination a[rel="next"]',
                'a[aria-label="Next"]',
                'a[title="Next"]',
                '.next a',
                'a:contains("Trang sau")',
                '.pagination .page-item:last-child a',
                'a[href*="page="]'
            ],
        }
    
    async def scrape_listings(self, max_pages: int = 10) -> List[PropertyListing]:
        """
        Scrape property listings from BatDongSan
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[PropertyListing]: List of scraped property listings
        """
        listings = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            page = await browser.new_page()
            
            # Set user agent and headers
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            try:
                # Try multiple starting URLs
                start_urls = [
                    f"{self.base_url}/ban-nha-dat",
                    f"{self.base_url}/ban-can-ho",
                    f"{self.base_url}/ban-nha-rieng",
                    f"{self.base_url}/ban-dat-nen"
                ]
                
                for start_url in start_urls:
                    try:
                        logger.info(f"Trying to scrape from: {start_url}")
                        await page.goto(start_url, wait_until='networkidle', timeout=30000)
                        await self.respectful_delay()
                        
                        # Check if page loaded successfully
                        page_content = await page.content()
                        if "Just a moment" in page_content or "Cloudflare" in page_content:
                            logger.warning(f"Cloudflare protection detected on {start_url}")
                            continue
                        
                        # Try to find listings
                        listing_elements = await self._find_listing_elements(page)
                        if listing_elements:
                            logger.info(f"Found {len(listing_elements)} listings on {start_url}")
                            break
                        else:
                            logger.warning(f"No listings found on {start_url}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error accessing {start_url}: {e}")
                        continue
                else:
                    logger.error("Could not access any BatDongSan URLs")
                    return listings
                
                page_num = 1
                while page_num <= max_pages:
                    logger.info(f"Scraping page {page_num} from BatDongSan")
                    
                    # Wait for listings to load with multiple selector attempts
                    listing_elements = await self._find_listing_elements(page)
                    
                    if not listing_elements:
                        logger.warning(f"No listing elements found on page {page_num}")
                        break
                    
                    # Parse each listing
                    for element in listing_elements:
                        try:
                            listing = await self.parse_listing_async(page, element)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.error(f"Error parsing listing: {e}")
                            continue
                    
                    # Check if there's a next page
                    next_button = await self._find_next_button(page)
                    if not next_button or page_num >= max_pages:
                        break
                    
                    # Go to next page
                    try:
                        await next_button.click()
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await self.respectful_delay()
                        page_num += 1
                    except Exception as e:
                        logger.error(f"Error navigating to next page: {e}")
                        break
                    
            except Exception as e:
                logger.error(f"Error during BatDongSan scraping: {e}")
                
            finally:
                await browser.close()
        
        logger.info(f"Total BatDongSan listings scraped: {len(listings)}")
        return listings
    
    async def _find_listing_elements(self, page: Page) -> List[Any]:
        """Find listing elements using multiple selector strategies"""
        for selector in self.selectors['listing_container']:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} listings with selector: {selector}")
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        return []
    
    async def _find_next_button(self, page: Page) -> Optional[Any]:
        """Find next page button using multiple selector strategies"""
        for selector in self.selectors['next_page']:
            try:
                button = await page.query_selector(selector)
                if button:
                    # Check if button is visible and clickable
                    is_visible = await button.is_visible()
                    if is_visible:
                        return button
            except Exception as e:
                logger.debug(f"Next button selector {selector} failed: {e}")
                continue
        
        return None
    
    async def _get_element_text(self, element: Any, selectors: List[str]) -> str:
        """Get text from element using multiple selector strategies"""
        for selector in selectors:
            try:
                sub_element = await element.query_selector(selector)
                if sub_element:
                    text = await sub_element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"Text selector {selector} failed: {e}")
                continue
        
        return ""
    
    async def _get_element_attribute(self, element: Any, selectors: List[str], attribute: str) -> str:
        """Get attribute from element using multiple selector strategies"""
        for selector in selectors:
            try:
                sub_element = await element.query_selector(selector)
                if sub_element:
                    value = await sub_element.get_attribute(attribute)
                    if value:
                        return value
            except Exception as e:
                logger.debug(f"Attribute selector {selector} failed: {e}")
                continue
        
        return ""
    
    async def parse_listing_async(self, page: Page, element: Any) -> Optional[PropertyListing]:
        """
        Parse a listing element asynchronously with fallback selectors
        
        Args:
            page: Playwright page object
            element: Listing element
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None
        """
        try:
            # Extract title and link
            title = await self._get_element_text(element, self.selectors['title'])
            if not title:
                title = "No title"
            
            link = await self._get_element_attribute(element, self.selectors['title'], 'href')
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Extract price
            price_text = await self._get_element_text(element, self.selectors['price'])
            price = self.clean_price(price_text) if price_text else 0.0
            
            # Extract area
            area_text = await self._get_element_text(element, self.selectors['area'])
            area = self.clean_area(area_text) if area_text else 0.0
            
            # Extract location
            location = await self._get_element_text(element, self.selectors['location'])
            if not location:
                location = "Unknown"
            
            # Extract image
            image_url = await self._get_element_attribute(element, self.selectors['image'], 'src')
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(self.base_url, image_url)
            
            # Extract property type
            property_type = await self._get_element_text(element, self.selectors['property_type'])
            if not property_type:
                property_type = "Unknown"
            
            # Extract bedrooms
            bedroom_text = await self._get_element_text(element, self.selectors['bedrooms'])
            bedrooms = None
            if bedroom_text:
                import re
                numbers = re.findall(r'\d+', bedroom_text)
                if numbers:
                    bedrooms = int(numbers[0])
            
            # Extract bathrooms
            bathroom_text = await self._get_element_text(element, self.selectors['bathrooms'])
            bathrooms = None
            if bathroom_text:
                import re
                numbers = re.findall(r'\d+', bathroom_text)
                if numbers:
                    bathrooms = int(numbers[0])
            
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
                raw_data={
                    'price_text': price_text,
                    'area_text': area_text,
                    'property_type': property_type,
                }
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Error parsing BatDongSan listing: {e}")
            return None
    
    def parse_listing(self, listing_element: Any) -> Optional[PropertyListing]:
        """
        Parse a single listing element (synchronous version for compatibility)
        
        Args:
            listing_element: Raw listing element from the page
            
        Returns:
            Optional[PropertyListing]: Parsed listing or None if parsing fails
        """
        # This method is kept for compatibility but the async version is preferred
        logger.warning("Using synchronous parse_listing - use parse_listing_async instead")
        return None


# Sample data for testing and development
SAMPLE_BATDONGSAN_DATA = [
    {
        "title": "Căn hộ 2 phòng ngủ tại Quận 1, TP.HCM",
        "location": "Quận 1, TP.HCM",
        "price": 2500000000,  # 2.5 billion VND
        "area": 65.0,  # 65 m²
        "price_per_m2": 38461538.46,
        "image_url": "https://example.com/image1.jpg",
        "link": "https://batdongsan.com.vn/ban-can-ho/can-ho-2-phong-ngu-quan-1",
        "property_type": "Căn hộ",
        "bedrooms": 2,
        "bathrooms": 2,
        "timestamp": datetime.now(),
        "source": "BatDongSan",
        "raw_data": {
            "price_text": "2.5 tỷ",
            "area_text": "65m²",
            "property_type": "Căn hộ"
        }
    },
    {
        "title": "Nhà riêng 3 tầng tại Quận 3, TP.HCM",
        "location": "Quận 3, TP.HCM", 
        "price": 8500000000,  # 8.5 billion VND
        "area": 120.0,  # 120 m²
        "price_per_m2": 70833333.33,
        "image_url": "https://example.com/image2.jpg",
        "link": "https://batdongsan.com.vn/ban-nha-rieng/nha-rieng-3-tang-quan-3",
        "property_type": "Nhà riêng",
        "bedrooms": 4,
        "bathrooms": 3,
        "timestamp": datetime.now(),
        "source": "BatDongSan",
        "raw_data": {
            "price_text": "8.5 tỷ",
            "area_text": "120m²",
            "property_type": "Nhà riêng"
        }
    }
] 