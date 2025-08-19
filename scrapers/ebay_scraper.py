"""
eBay UK Scraper Module
Scrapes GPU listings from eBay UK marketplace
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import json
import re

from .base_scraper import BaseScraper


class EBayScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.ebay.co.uk"
        self.search_url = "https://www.ebay.co.uk/sch/i.html"
        
        # eBay-specific configuration
        self.max_pages = min(config.limits.max_pages, 10)  # eBay limits
        self.results_per_page = 50  # eBay default
        
        # Search parameters for GPU listings
        self.search_params = {
            '_nkw': '',  # Will be filled with search terms
            '_sacat': '27386',  # Computer Components & Parts > Graphics/Video Cards
            'LH_BIN': '1',  # Buy It Now only
            'LH_ItemCondition': '3000|4000|5000',  # Used, Very Good, Excellent
            '_udlo': '50',   # Minimum price £50
            '_udhi': '2000', # Maximum price £2000
            'rt': 'nc',     # No store categories
            '_ipg': '50',   # Items per page
            '_pgn': '1'     # Page number
        }

    async def scrape_gpu_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape GPU listings from eBay UK
        """
        self.logger.info("Starting eBay UK GPU scraping...")
        
        # Check robots.txt compliance
        if not self.check_robots_txt(self.base_url):
            self.logger.warning("Robots.txt may restrict scraping")
        
        all_listings = []
        search_terms = self.config.get_search_terms()
        
        async with self:  # Use async context manager
            for search_term in search_terms:
                self.logger.info(f"Searching eBay for: {search_term}")
                
                listings = await self._search_gpu_term(search_term)
                all_listings.extend(listings)
                
                # Respect rate limits between searches
                await asyncio.sleep(self.config.limits.request_delay)
                
                if len(all_listings) >= self.config.limits.max_results_per_site:
                    break
        
        # Remove duplicates and filter
        unique_listings = self._deduplicate_listings(all_listings)
        self.logger.info(f"Found {len(unique_listings)} unique eBay listings")
        
        return unique_listings[:self.config.limits.max_results_per_site]

    async def _search_gpu_term(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for a specific GPU term across multiple pages
        """
        listings = []
        
        for page in range(1, self.max_pages + 1):
            self.logger.debug(f"Scraping eBay page {page} for '{search_term}'")
            
            # Build search URL
            params = self.search_params.copy()
            params['_nkw'] = search_term
            params['_pgn'] = page
            
            search_url = f"{self.search_url}?{urlencode(params)}"
            
            # Fetch page content
            html_content = await self.make_request(search_url)
            if not html_content:
                continue
            
            # Parse listings from page
            page_listings = await self._parse_search_results(html_content, search_term)
            listings.extend(page_listings)
            
            # Check if we've reached the end
            if len(page_listings) < self.results_per_page:
                break
                
            # Rate limiting between pages
            await asyncio.sleep(self.config.limits.request_delay)
        
        return listings

    async def _parse_search_results(self, html_content: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Parse eBay search results page
        """
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find listing containers
        listing_containers = soup.find_all('div', {'class': 's-item'})
        
        for container in listing_containers:
            try:
                listing_data = self.parse_listing(container)
                if listing_data and self.is_gpu_listing(listing_data['title']):
                    listing_data['search_term'] = search_term
                    listings.append(listing_data)
            except Exception as e:
                self.logger.debug(f"Failed to parse eBay listing: {e}")
                continue
        
        self.logger.debug(f"Parsed {len(listings)} listings from eBay page")
        return listings

    def parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """
        Parse a single eBay listing element
        """
        try:
            # Extract basic information
            title_elem = listing_element.find('h3', class_='s-item__title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if title.lower().startswith('shop on ebay'):
                return None  # Skip promotional items
            
            # Extract URL
            link_elem = listing_element.find('a', class_='s-item__link')
            url = link_elem.get('href') if link_elem else None
            
            # Extract price
            price_elem = listing_element.find('span', class_='s-item__price')
            price_text = price_elem.get_text(strip=True) if price_elem else ''
            
            # Extract condition
            condition_elem = listing_element.find('span', class_='SECONDARY_INFO')
            condition = condition_elem.get_text(strip=True) if condition_elem else ''
            
            # Extract shipping info
            shipping_elem = listing_element.find('span', class_='s-item__shipping')
            shipping = shipping_elem.get_text(strip=True) if shipping_elem else ''
            
            # Extract location
            location_elem = listing_element.find('span', class_='s-item__location')
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Extract seller info
            seller_elem = listing_element.find('span', class_='s-item__seller-info-text')
            seller_info = seller_elem.get_text(strip=True) if seller_elem else ''
            
            # Extract listing type (auction vs buy it now)
            listing_type = 'Buy It Now'  # We filtered for BIN only
            
            # Extract image URL
            img_elem = listing_element.find('img', class_='s-item__image')
            image_url = img_elem.get('src') if img_elem else None
            
            # Check for "SOLD" or "SOLD LISTINGS"
            sold_elem = listing_element.find('span', class_='s-item__title--tag')
            is_sold = sold_elem and 'sold' in sold_elem.get_text().lower()
            
            return {
                'title': title,
                'url': url,
                'price': price_text,
                'condition': condition,
                'shipping': shipping,
                'location': location,
                'seller_info': seller_info,
                'listing_type': listing_type,
                'image_url': image_url,
                'is_sold': is_sold,
                'marketplace': 'eBay UK'
            }
            
        except Exception as e:
            self.logger.debug(f"Error parsing eBay listing element: {e}")
            return None

    def _deduplicate_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate listings based on URL and title similarity
        """
        seen_urls = set()
        unique_listings = []
        
        for listing in listings:
            url = listing.get('url', '')
            title = listing.get('title', '')
            
            # Skip sold listings
            if listing.get('is_sold', False):
                continue
            
            # Use URL as primary deduplication key
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_listings.append(listing)
            elif not url:
                # For listings without URL, use title-based deduplication
                title_hash = hash(title.lower()[:50])  # First 50 chars
                if title_hash not in seen_urls:
                    seen_urls.add(title_hash)
                    unique_listings.append(listing)
        
        return unique_listings

    async def get_listing_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information from individual eBay listing page
        """
        try:
            html_content = await self.make_request(listing_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract detailed description
            desc_elem = soup.find('div', {'id': 'desc_div'}) or soup.find('div', class_='u-flL condText')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract item specifics
            specifics = {}
            specifics_section = soup.find('div', {'id': 'viTabs_0_is'})
            if specifics_section:
                labels = specifics_section.find_all('dt', class_='attrLabels')
                values = specifics_section.find_all('dd', class_='attrValues')
                
                for label, value in zip(labels, values):
                    key = label.get_text(strip=True).rstrip(':')
                    val = value.get_text(strip=True)
                    specifics[key] = val
            
            # Extract multiple images
            image_urls = []
            img_elements = soup.find_all('img', {'id': re.compile(r'icImg')})
            for img in img_elements:
                src = img.get('src')
                if src and src.startswith('http'):
                    image_urls.append(src)
            
            return {
                'description': description,
                'item_specifics': specifics,
                'image_urls': image_urls
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get eBay listing details: {e}")
            return None

    def extract_item_id(self, url: str) -> Optional[str]:
        """
        Extract eBay item ID from listing URL
        """
        if not url:
            return None
        
        # eBay item URLs contain the item ID
        match = re.search(r'/itm/(\d+)', url)
        if match:
            return match.group(1)
        
        # Alternative pattern
        match = re.search(r'item=(\d+)', url)
        if match:
            return match.group(1)
        
        return None


# Test function for eBay scraper
async def test_ebay_scraper():
    """Test the eBay scraper functionality"""
    from config.settings import ScraperConfig
    
    config = ScraperConfig()
    scraper = EBayScraper(config)
    
    # Test with a single search term
    async with scraper:
        listings = await scraper._search_gpu_term("RTX 4070")
        
        print(f"Found {len(listings)} listings for RTX 4070")
        for i, listing in enumerate(listings[:3]):  # Show first 3
            print(f"\n{i+1}. {listing['title']}")
            print(f"   Price: {listing['price']}")
            print(f"   Condition: {listing['condition']}")
            print(f"   URL: {listing['url']}")


if __name__ == "__main__":
    asyncio.run(test_ebay_scraper())