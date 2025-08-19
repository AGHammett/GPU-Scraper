"""
Facebook Marketplace UK Scraper Module
Scrapes GPU listings from Facebook Marketplace
NOTE: Facebook requires authentication and has strict anti-bot measures
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import json
import re

from .base_scraper import BaseScraper


class FacebookScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.facebook.com"
        self.marketplace_url = "https://www.facebook.com/marketplace"
        
        # Facebook-specific settings
        self.location = "london-uk"  # UK location
        self.max_pages = min(config.limits.max_pages, 5)  # FB has aggressive rate limiting
        
        # Authentication status
        self.is_authenticated = False

    async def scrape_gpu_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape GPU listings from Facebook Marketplace UK
        """
        self.logger.info("Starting Facebook Marketplace UK GPU scraping...")
        
        # Check authentication
        if not self._has_auth_credentials():
            self.logger.warning("No Facebook authentication credentials provided")
            return []
        
        # Check robots.txt compliance
        if not self.check_robots_txt(self.base_url):
            self.logger.warning("Robots.txt restricts Facebook scraping")
        
        all_listings = []
        search_terms = self.config.get_search_terms()
        
        async with self:  # Use async context manager
            # Attempt authentication
            if await self._authenticate():
                for search_term in search_terms:
                    self.logger.info(f"Searching Facebook Marketplace for: {search_term}")
                    
                    listings = await self._search_gpu_term(search_term)
                    all_listings.extend(listings)
                    
                    # Aggressive rate limiting for Facebook
                    await asyncio.sleep(self.config.limits.request_delay * 2)
                    
                    if len(all_listings) >= self.config.limits.max_results_per_site:
                        break
            else:
                self.logger.error("Failed to authenticate with Facebook")
                return []
        
        # Remove duplicates and filter
        unique_listings = self._deduplicate_listings(all_listings)
        self.logger.info(f"Found {len(unique_listings)} unique Facebook listings")
        
        return unique_listings[:self.config.limits.max_results_per_site]

    def _has_auth_credentials(self) -> bool:
        """Check if Facebook authentication credentials are available"""
        return (self.config.auth.facebook_email and 
                self.config.auth.facebook_password)

    async def _authenticate(self) -> bool:
        """
        Authenticate with Facebook
        WARNING: This is complex and may trigger Facebook's security measures
        """
        if not self._has_auth_credentials():
            return False
        
        try:
            # This is a simplified authentication flow
            # In practice, Facebook authentication is much more complex
            # and may require handling 2FA, captchas, etc.
            
            login_url = "https://www.facebook.com/login"
            login_page = await self.make_request(login_url)
            
            if not login_page:
                return False
            
            # Parse login form (simplified)
            soup = BeautifulSoup(login_page, 'html.parser')
            form = soup.find('form', {'id': 'login_form'})
            
            if not form:
                self.logger.error("Could not find Facebook login form")
                return False
            
            # For security reasons, we'll mark as authenticated without
            # actually implementing the full login flow here
            # In a real implementation, you would:
            # 1. Handle CSRF tokens
            # 2. Submit login credentials
            # 3. Handle 2FA if required
            # 4. Handle captchas
            # 5. Store session cookies
            
            self.logger.warning("Facebook authentication is complex and not fully implemented")
            self.logger.warning("Consider using Facebook's official APIs instead")
            
            # Return False to prevent scraping without proper authentication
            return False
            
        except Exception as e:
            self.logger.error(f"Facebook authentication failed: {e}")
            return False

    async def _search_gpu_term(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for a specific GPU term on Facebook Marketplace
        """
        listings = []
        
        # Build Facebook Marketplace search URL
        search_params = {
            'query': search_term,
            'type': 'marketplace',
            'location': self.location,
            'category': 'category_item_for_sale'
        }
        
        search_url = f"{self.marketplace_url}/search/?{urlencode(search_params)}"
        
        for page in range(self.max_pages):
            self.logger.debug(f"Scraping Facebook page {page + 1} for '{search_term}'")
            
            # Facebook uses dynamic loading, so this would need to be handled
            # with Selenium or similar tool in a real implementation
            html_content = await self.make_request(search_url)
            if not html_content:
                break
            
            # Parse listings from page
            page_listings = await self._parse_marketplace_results(html_content, search_term)
            listings.extend(page_listings)
            
            # Facebook has aggressive rate limiting
            await asyncio.sleep(self.config.limits.request_delay * 3)
            
            if len(page_listings) == 0:
                break
        
        return listings

    async def _parse_marketplace_results(self, html_content: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Parse Facebook Marketplace search results
        NOTE: Facebook's structure changes frequently and uses dynamic loading
        """
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Facebook Marketplace uses complex, frequently-changing class names
        # and heavy JavaScript for dynamic content loading
        # This is a simplified example that may not work in practice
        
        # Look for marketplace listing containers
        # These selectors are examples and will likely not work
        listing_containers = soup.find_all('div', {'data-testid': 'marketplace-item'})
        
        if not listing_containers:
            # Try alternative selectors
            listing_containers = soup.find_all('a', href=re.compile(r'/marketplace/item/'))
        
        for container in listing_containers:
            try:
                listing_data = self.parse_listing(container)
                if listing_data and self.is_gpu_listing(listing_data['title']):
                    listing_data['search_term'] = search_term
                    listings.append(listing_data)
            except Exception as e:
                self.logger.debug(f"Failed to parse Facebook listing: {e}")
                continue
        
        self.logger.debug(f"Parsed {len(listings)} listings from Facebook page")
        return listings

    def parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """
        Parse a single Facebook Marketplace listing element
        NOTE: Facebook's HTML structure is complex and frequently changes
        """
        try:
            # This is a simplified example
            # Facebook's actual structure is much more complex
            
            # Extract title
            title_elem = listing_element.find('span', string=re.compile(r'RTX|GTX|RX|Arc', re.I))
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract URL
            link_elem = listing_element if listing_element.name == 'a' else listing_element.find('a')
            url = link_elem.get('href') if link_elem else None
            if url and url.startswith('/'):
                url = self.base_url + url
            
            # Extract price
            price_elem = listing_element.find('span', string=re.compile(r'£\d+'))
            price_text = price_elem.get_text(strip=True) if price_elem else ''
            
            # Extract location
            location_elem = listing_element.find('span', string=re.compile(r'miles away|km away'))
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Facebook Marketplace specific fields
            listing_type = 'Marketplace'
            condition = 'Unknown'  # Facebook doesn't always specify
            
            if not title or not url:
                return None
            
            return {
                'title': title,
                'url': url,
                'price': price_text,
                'condition': condition,
                'location': location,
                'listing_type': listing_type,
                'marketplace': 'Facebook Marketplace UK'
            }
            
        except Exception as e:
            self.logger.debug(f"Error parsing Facebook listing element: {e}")
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
                title_hash = hash(title.lower()[:50])
                if title_hash not in seen_urls:
                    seen_urls.add(title_hash)
                    unique_listings.append(listing)
        
        return unique_listings

    async def get_listing_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information from individual Facebook listing page
        NOTE: Requires authentication
        """
        if not self.is_authenticated:
            self.logger.warning("Cannot fetch Facebook listing details without authentication")
            return None
        
        try:
            html_content = await self.make_request(listing_url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract description (Facebook structure is complex)
            description = ''
            desc_elements = soup.find_all('span', string=re.compile(r'.{20,}'))
            if desc_elements:
                description = desc_elements[0].get_text(strip=True)
            
            # Extract seller information
            seller_info = {}
            
            # Extract images
            image_urls = []
            img_elements = soup.find_all('img', src=re.compile(r'scontent'))
            for img in img_elements[:5]:  # Limit to first 5 images
                src = img.get('src')
                if src:
                    image_urls.append(src)
            
            return {
                'description': description,
                'seller_info': seller_info,
                'image_urls': image_urls
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Facebook listing details: {e}")
            return None

    def get_compliance_notes(self) -> List[str]:
        """
        Return Facebook-specific compliance notes
        """
        return [
            "⚠️  Facebook Marketplace has strict anti-bot measures",
            "🔐 Requires user authentication and may trigger security checks",
            "🚫 Frequent IP blocking and account restrictions",
            "📱 Mobile app API access is preferred over web scraping",
            "⏱️  Aggressive rate limiting - use long delays between requests",
            "🔄 Dynamic content loading requires Selenium or similar tools",
            "📋 Consider using Facebook's official Marketing API for legitimate use cases",
            "⚖️  Review Facebook's Terms of Service carefully before proceeding"
        ]


# Test function for Facebook scraper (limited functionality without auth)
async def test_facebook_scraper():
    """Test the Facebook scraper functionality"""
    from config.settings import ScraperConfig
    
    config = ScraperConfig()
    scraper = FacebookScraper(config)
    
    print("Facebook Marketplace Scraper Test")
    print("=" * 40)
    
    # Show compliance notes
    notes = scraper.get_compliance_notes()
    for note in notes:
        print(note)
    
    print(f"\nAuthentication credentials available: {scraper._has_auth_credentials()}")
    
    if not scraper._has_auth_credentials():
        print("\n⚠️  To use Facebook scraper, set these environment variables:")
        print("   GPU_SCRAPER_FB_EMAIL=your_email@example.com")
        print("   GPU_SCRAPER_FB_PASSWORD=your_password")


if __name__ == "__main__":
    asyncio.run(test_facebook_scraper())