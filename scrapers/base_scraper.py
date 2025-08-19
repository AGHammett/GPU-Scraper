"""
Base scraper class with common functionality
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import aiohttp
from urllib.robotparser import RobotFileParser


class BaseScraper(ABC):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.config.limits.timeout)
        self.session = aiohttp.ClientSession(
            headers=self.config.get_request_headers(),
            timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def make_request(self, url: str, **kwargs) -> Optional[str]:
        """Make an HTTP request with error handling and rate limiting"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            # Rate limiting
            await asyncio.sleep(self.config.limits.request_delay)
            
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    self.logger.warning(f"Rate limited on {url}, waiting...")
                    await asyncio.sleep(10)
                    return None
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None

    def check_robots_txt(self, base_url: str, user_agent: str = "*") -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            robots_url = f"{base_url}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(user_agent, base_url)
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt for {base_url}: {e}")
            return True  # Assume allowed if we can't check

    @abstractmethod
    async def scrape_gpu_listings(self) -> List[Dict[str, Any]]:
        """Scrape GPU listings from the marketplace"""
        pass

    @abstractmethod
    def parse_listing(self, listing_element) -> Optional[Dict[str, Any]]:
        """Parse a single listing element into structured data"""
        pass

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
            
        import re
        # Remove currency symbols and common text
        cleaned = re.sub(r'[£$€,]', '', price_text.lower())
        cleaned = re.sub(r'(ono|or best offer|obo)', '', cleaned)
        
        # Extract first number
        match = re.search(r'(\d+(?:\.\d{2})?)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def is_gpu_listing(self, title: str, description: str = "") -> bool:
        """Check if listing is likely a GPU based on title/description"""
        text = (title + " " + description).lower()
        
        gpu_indicators = [
            'rtx', 'gtx', 'radeon', 'rx ', 'arc', 'graphics card', 
            'gpu', 'video card', 'nvidia', 'amd', 'intel'
        ]
        
        return any(indicator in text for indicator in gpu_indicators)