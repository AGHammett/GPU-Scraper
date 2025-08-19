"""
Gumtree UK Scraper Module
Scrapes GPU listings from Gumtree UK marketplace
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import json
import re

from .base_scraper import BaseScraper


class GumtreeScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.gumtree.com"
        self.search_url = "https://www.gumtree.com/search"
        
        # Gumtree-specific configuration
        self.max_pages = min(config.limits.max_pages, 8)  # Gumtree pagination
        self.results_per_page = 20  # Gumtree default
        
        # Search parameters for GPU listings
        self.search_params = {
            'search_category': 'computers-software',
            'search_location': 'united-kingdom',
            'distance': '0',  # All of UK
            'q': '',  # Will be filled with search terms
            'search_scope': 'title_and_description',
            'page': '1'
        }

    async def scrape_gpu_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape GPU listings from Gumtree UK
        """
        self.logger.info("Starting Gumtree UK GPU scraping...")
        
        # Check robots.txt compliance
        if not self.check_robots_txt(self.base_url):
            self.logger.warning("Robots.txt may restrict scraping")
        
        all_listings = []
        search_terms = self.config.get_search_terms()
        
        async with self:  # Use async context manager
            for search_term in search_terms:
                self.logger.info(f"Searching Gumtree for: {search_term}")
                
                listings = await self._search_gpu_term(search_term)
                all_listings.extend(listings)
                
                # Respect rate limits between searches
                await asyncio.sleep(self.config.limits.request_delay)
                
                if len(all_listings) >= self.config.limits.max_results_per_site:
                    break
        
        # Remove duplicates and filter
        unique_listings = self._deduplicate_listings(all_listings)
        self.logger.info(f"Found {len(unique_listings)} unique Gumtree listings")
        
        return unique_listings[:self.config.limits.max_results_per_site]

    async def _search_gpu_term(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for a specific GPU term across multiple pages
        """
        listings = []
        
        for page in range(1, self.max_pages + 1):
            self.logger.debug(f"Scraping Gumtree page {page} for '{search_term}'")
            
            # Build search URL
            params = self.search_params.copy()
            params['q'] = search_term
            params['page'] = page
            
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
        Parse Gumtree search results page
        """
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find listing containers - Gumtree uses various selectors
        listing_containers = soup.find_all('div', class_=re.compile(r'listing-maxi')) or \
                           soup.find_all('article', class_=re.compile(r'listing-maxi')) or \
                           soup.find_all('div', class_=re.compile(r'natural'))
        
        for container in listing_containers:
            try:
                listing_data = self.parse_listing(container)
                if listing_data and self.is_gpu_listing(listing_data['title']):
                    listing_data['search_term'] = search_term
                    listings.append(listing_data)
            except Exception as e:
                self.logger.debug(f"Failed to parse Gumtree listing: {e}")
                continue
        
        self.logger.debug(f"Parsed {len(listings)} listings from Gumtree page")
        return listings

    def parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """
        Parse a single Gumtree listing element
        """
        try:
            # Extract title
            title_elem = listing_element.find('a', class_=re.compile(r'listing-link')) or \
                        listing_element.find('h2', class_=re.compile(r'listing-title')) or \
                        listing_element.find('a', href=re.compile(r'/ad/'))
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title:
                return None
            
            # Extract URL
            url = title_elem.get('href') if title_elem else None
            if url and url.startswith('/'):
                url = urljoin(self.base_url, url)
            
            # Extract price
            price_elem = listing_element.find('span', class_=re.compile(r'listing-price')) or \
                        listing_element.find('strong', class_=re.compile(r'amount')) or \
                        listing_element.find('span', string=re.compile(r'£\d+'))
            
            price_text = price_elem.get_text(strip=True) if price_elem else ''
            
            # Extract location
            location_elem = listing_element.find('span', class_=re.compile(r'listing-location')) or \
                           listing_element.find('div', class_=re.compile(r'location'))
            
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Extract date/time posted
            date_elem = listing_element.find('span', class_=re.compile(r'listing-posted-date')) or \
                       listing_element.find('time')
            
            posted_date = date_elem.get_text(strip=True) if date_elem else ''
            
            # Extract description preview
            desc_elem = listing_element.find('p', class_=re.compile(r'listing-description')) or \
                       listing_element.find('div', class_=re.compile(r'description'))
            
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract image URL
            img_elem = listing_element.find('img', class_=re.compile(r'listing-thumbnail')) or \
                      listing_element.find('img', src=re.compile(r'i\.ebayimg|gumtree'))
            
            image_url = img_elem.get('src') if img_elem else None
            
            # Extract seller info
            seller_elem = listing_element.find('span', class_=re.compile(r'seller')) or \
                         listing_element.find('div', class_=re.compile(r'seller'))
            
            seller_info = seller_elem.get_text(strip=True) if seller_elem else ''
            
            # Check for featured/urgent ads
            is_featured = bool(listing_element.find('span', class_=re.compile(r'featured|urgent')))
            
            return {
                'title': title,
                'url': url,
                'price': price_text,
                'location': location,
                'posted_date': posted_date,
                'description': description,
                'image_url': image_url,
                'seller_info': seller_info,
                'is_featured': is_featured,
                'marketplace': 'Gumtree UK'
            }
            
        except Exception as e:
            self.logger.debug(f"Error parsing Gumtree listing element: {e}")
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
        Fetch detailed information from individual Gumtree listing page
        """
        try:
            html_content = await self.make_request(listing_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract full description
            desc_elem = soup.find('div', class_=re.compile(r'ad-description')) or \
                       soup.find('section', class_=re.compile(r'description'))
            
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract seller information
            seller_info = {}
            seller_section = soup.find('div', class_=re.compile(r'seller-info|seller-details'))
            if seller_section:
                seller_name = seller_section.find('span', class_=re.compile(r'seller-name'))
                if seller_name:
                    seller_info['name'] = seller_name.get_text(strip=True)
                
                # Extract join date, verification status, etc.
                seller_details = seller_section.find_all('span')
                for detail in seller_details:
                    text = detail.get_text(strip=True)
                    if 'member since' in text.lower():
                        seller_info['member_since'] = text
                    elif 'verified' in text.lower():
                        seller_info['verified'] = True
            
            # Extract multiple images
            image_urls = []
            img_elements = soup.find_all('img', src=re.compile(r'gumtree|apollo'))
            for img in img_elements:
                src = img.get('src')
                if src and 'thumb' not in src and src.startswith('http'):
                    image_urls.append(src)
            
            # Extract ad details/specifications
            ad_details = {}
            details_section = soup.find('div', class_=re.compile(r'ad-details|attributes'))
            if details_section:
                labels = details_section.find_all('dt') or details_section.find_all('strong')
                values = details_section.find_all('dd') or details_section.find_all('span')
                
                for label, value in zip(labels, values):
                    key = label.get_text(strip=True).rstrip(':')
                    val = value.get_text(strip=True)
                    if key and val:
                        ad_details[key] = val
            
            return {
                'description': description,
                'seller_info': seller_info,
                'image_urls': image_urls,
                'ad_details': ad_details
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Gumtree listing details: {e}")
            return None

    def extract_ad_id(self, url: str) -> Optional[str]:
        """
        Extract Gumtree ad ID from listing URL
        """
        if not url:
            return None
        
        # Gumtree URLs typically contain the ad ID
        match = re.search(r'/ad/(\d+)', url)
        if match:
            return match.group(1)
        
        # Alternative pattern
        match = re.search(r'adId=(\d+)', url)
        if match:
            return match.group(1)
        
        return None

    def get_compliance_notes(self) -> List[str]:
        """
        Return Gumtree-specific compliance notes
        """
        return [
            "✅ Gumtree generally allows web scraping for personal use",
            "⚠️  Respect rate limits - use delays between requests",
            "🔍 Check robots.txt before scraping",
            "📋 Review Gumtree's Terms of Service for current policies",
            "🏢 For commercial use, consider contacting Gumtree directly",
            "🛡️  Use proper User-Agent headers",
            "⏱️  Implement reasonable request delays (2+ seconds)",
            "📊 Don't overload their servers with excessive requests"
        ]


# Test function for Gumtree scraper
async def test_gumtree_scraper():
    """Test the Gumtree scraper functionality"""
    from config.settings import ScraperConfig
    
    config = ScraperConfig()
    scraper = GumtreeScraper(config)
    
    print("Gumtree UK Scraper Test")
    print("=" * 30)
    
    # Show compliance notes
    notes = scraper.get_compliance_notes()
    for note in notes:
        print(note)
    
    # Test with a single search term
    async with scraper:
        listings = await scraper._search_gpu_term("RTX 4070")
        
        print(f"\nFound {len(listings)} listings for RTX 4070")
        for i, listing in enumerate(listings[:3]):  # Show first 3
            print(f"\n{i+1}. {listing['title']}")
            print(f"   Price: {listing['price']}")
            print(f"   Location: {listing['location']}")
            print(f"   URL: {listing['url']}")


if __name__ == "__main__":
    asyncio.run(test_gumtree_scraper())